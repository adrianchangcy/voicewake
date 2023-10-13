from django.contrib.auth import get_user_model
from django.db import connection
from django.db import transaction

#apps
from voicewake.services import *
from voicewake.models import *
from django.conf import settings


def cronjob_ban_events():

    #as long as quantity of event_reports rows is not a factor, we delete all of them after cron

    #ensure not to select events that are too new
    maximum_when_created = get_datetime_now() - timedelta(seconds=settings.BAN_EVENT_AGE_SECONDS)

    #we delete reports of events that do not meet ban conditions
    with connection.cursor() as cursor:

        cursor.execute(
            '''
                WITH
                distinct_reported_events AS (
                    SELECT DISTINCT reported_event_id
                    FROM event_reports
                    ORDER BY reported_event_id ASC
                    LIMIT %s
                ),
                events_not_to_ban AS (
                    SELECT events.id
                    FROM events
                    INNER JOIN distinct_reported_events ON events.id = distinct_reported_events.reported_event_id
                    WHERE events.dislike_count < %s
                    OR (events.dislike_count::float / (events.like_count + events.dislike_count)) < %s
                    OR events.when_created > %s
                    OR events.is_banned IS TRUE
                )
                DELETE FROM event_reports AS er
                USING events_not_to_ban AS entb
                WHERE er.reported_event_id = entb.id
            ''',
            params=(
                settings.BAN_EVENT_QUANTITY_PER_CRON,
                settings.BAN_EVENT_DISLIKE_COUNT,
                settings.BAN_EVENT_DISLIKE_RATIO,
                maximum_when_created,
            )
        )

    #for events we are about to ban, we get count of those users' event_report_bans
    #this is to determine the  appropriate banned_until value

    #must cast any one column as float for the ratio to work
    #otherwise, since all of them are int, we'd get 0
    with transaction.atomic():

        events_to_ban = Events.objects.prefetch_related(
            'user', 'event_role', 'event_room'
        ).select_for_update(
            of=('self', 'event_room')
        ).raw(
            '''
                WITH
                distinct_reported_events AS (
                    SELECT DISTINCT reported_event_id
                    FROM event_reports
                    ORDER BY reported_event_id ASC
                    LIMIT %s
                )
                SELECT events.*,
                (
                    SELECT COUNT(*) FROM events as events2
                    WHERE events2.user_id = events.user_id
                    AND events2.is_banned IS TRUE
                ) as ban_count
                FROM events
                RIGHT JOIN distinct_reported_events ON distinct_reported_events.reported_event_id = events.id
                WHERE events.dislike_count >= %s
                AND (events.dislike_count::float / (events.like_count + events.dislike_count)) >= %s
                AND events.when_created <= %s
                AND events.is_banned IS FALSE
            ''',
            params=(
                settings.BAN_EVENT_QUANTITY_PER_CRON,
                settings.BAN_EVENT_DISLIKE_COUNT,
                settings.BAN_EVENT_DISLIKE_RATIO,
                maximum_when_created,
            )
        )

        print(str(len(events_to_ban)) + ' events to ban')

        #ban
        #we will likely get multiple events from the same user here
        #to accurately set banned_until on a per-event basis, we track and update ban_count here

        datetime_now = get_datetime_now()
        user_details = {}   #keeps track of ban_count and banned_until

        event_room_ids = []
        bulk_event_rooms = []
        generic_status_deleted = GenericStatuses.objects.get(generic_status_name='deleted')
        generic_status_incomplete = GenericStatuses.objects.get(generic_status_name='incomplete')

        for x in range(len(events_to_ban)):

            events_to_ban[x].is_banned = True
            events_to_ban[x].generic_status = generic_status_deleted

            #track user and ban_count for cases of multiple events retrieved with same user
            user_id = events_to_ban[x].user.id

            if user_id in user_details:

                banned_until = datetime_now + timedelta(days=(
                    settings.BAN_EVENT_DURATION_PER_BAN_DAYS * user_details[user_id]['ban_count']
                ))

                user_details[user_id]['ban_count'] = user_details[user_id]['ban_count'] + 1
                user_details[user_id]['banned_until'] = banned_until

            else:

                banned_until = datetime_now + timedelta(days=(
                    settings.BAN_EVENT_DURATION_PER_BAN_DAYS * events_to_ban[x].ban_count
                ))

                user_details[user_id] = {
                    'ban_count': events_to_ban[x].ban_count + 1,
                    'banned_until': banned_until
                }

            current_event_role_name = events_to_ban[x].event_role.event_role_name
            expected_generic_status = None

            if current_event_role_name == 'originator':

                expected_generic_status = generic_status_deleted

            elif current_event_role_name == 'responder':

                expected_generic_status = generic_status_incomplete

            else:

                raise ValueError('Error when evaluating event_role_name.')

            #prepare to handle event_room
            #on edge case where event_room can be both deleted/incomplete, deleted takes precedence
            event_room_id = events_to_ban[x].event_room.id

            if event_room_id not in event_room_ids:

                event_room_ids.append(event_room_id)

                bulk_event_rooms.append(EventRooms(
                    pk=event_room_id,
                    generic_status=expected_generic_status,
                    when_locked=None,
                    is_replying=None,
                    locked_for_user=None
                ))

            elif (
                current_event_role_name == 'originator' and
                bulk_event_rooms[event_room_ids.index(event_room_id)].generic_status != generic_status_deleted
            ):

                #ensure deleted takes precedence over incomplete
                bulk_event_rooms[event_room_ids.index(event_room_id)].generic_status = generic_status_deleted

        #update events
        Events.objects.bulk_update(events_to_ban, ('is_banned', 'generic_status',))

        #update event_rooms
        EventRooms.objects.bulk_update(bulk_event_rooms, ('generic_status', 'when_locked', 'is_replying', 'locked_for_user',))

    #prepare users for update
    bulk_users = []

    for user_id in user_details:

        bulk_users.append(get_user_model()(
            pk=user_id,
            banned_until=user_details[user_id]['banned_until']
        ))

    #update users
    get_user_model().objects.bulk_update(bulk_users, ('banned_until',))

    #delete event_reports
    EventReports.objects.filter(reported_event__in=events_to_ban).delete()


def cronjob_reset_reply_choice_overdue():

    #have this to reduce the chances of cronjob + auto-cancel reply from frontend colliding
    #which would be fine, but it's better for UX
    extra_seconds = 60

    max_when_locked = get_datetime_now() - timedelta(seconds=(settings.EVENT_ROOM_REPLY_CHOICE_EXPIRY_SECONDS + extra_seconds))

    with connection.cursor() as cursor:

        cursor.execute(
            '''
            WITH selected_event_rooms AS (
                SELECT * FROM event_rooms
                WHERE is_replying IS FALSE
                AND locked_for_user_id IS NOT NULL
                AND when_locked <= %s
                LIMIT %s
            )
            UPDATE event_rooms
            SET is_replying = NULL, locked_for_user_id = NULL, when_locked = NULL
            FROM selected_event_rooms
            WHERE event_rooms.id = selected_event_rooms.id
            ''',
            params=(
                max_when_locked,
                settings.EVENT_ROOM_UNDO_REPLY_QUANTITY_PER_CRON,
            )
        )


def cronjob_reset_replying_overdue():

    #have this to reduce the chances of cronjob + auto-cancel reply from frontend colliding
    #which would be fine, but it's better for UX
    extra_seconds = 60

    max_when_locked = get_datetime_now() - timedelta(seconds=(settings.EVENT_ROOM_REPLY_EXPIRY_SECONDS + extra_seconds))

    with connection.cursor() as cursor:

        cursor.execute(
            '''
            WITH selected_event_rooms AS (
                SELECT * FROM event_rooms
                WHERE is_replying IS TRUE
                AND locked_for_user_id IS NOT NULL
                AND when_locked <= %s
                LIMIT %s
            )
            UPDATE event_rooms
            SET is_replying = NULL, locked_for_user_id = NULL, when_locked = NULL
            FROM selected_event_rooms
            WHERE event_rooms.id = selected_event_rooms.id
            ''',
            params=(
                max_when_locked,
                settings.EVENT_ROOM_UNDO_REPLY_QUANTITY_PER_CRON,
            )
        )






