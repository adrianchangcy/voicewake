from django.contrib.auth import get_user_model

#apps
from voicewake.services import *
from voicewake.models import *
from django.conf import settings


def cronjob_ban_events(self):

    #as long as quantity of event_reports rows is not a factor, we delete all of them after cron

    #ensure not to select events that are too new
    maximum_when_created = get_datetime_now() - timedelta(seconds=settings.BAN_EVENT_AGE_SECONDS)

    #for events we are about to ban, we get count of those users' event_report_bans
    #this is to determine the  appropriate banned_until value

    #must cast any one column as float for the ratio to work
    #otherwise, since all of them are int, we'd get 0
    events_to_ban = Events.objects.prefetch_related('user').raw(
        '''
            SELECT events.*,
            (
                SELECT COUNT(*) FROM events as events2
                WHERE events2.user_id = events.user_id
                AND events2.is_banned IS TRUE
            ) as ban_count
            FROM events
            RIGHT JOIN event_reports ON event_reports.reported_event_id = events.id
            WHERE events.dislike_count >= %s
            AND (events.dislike_count::float / (events.like_count + events.dislike_count)) >= %s
            AND events.when_created <= %s
            ORDER BY events.when_created ASC
            LIMIT %s
        ''',
        params=(
            settings.BAN_EVENT_DISLIKE_COUNT,
            settings.BAN_EVENT_DISLIKE_RATIO,
            maximum_when_created,
            settings.BAN_EVENT_QUANTITY_PER_CRON,
        )
    )

    print(str(len(events_to_ban)) + ' events to ban')

    #ban
    #we will likely get multiple events from the same user here
    #to accurately set banned_until on a per-event basis, we track and update ban_count here

    datetime_now = get_datetime_now()
    user_details = {}   #keeps track of ban_count and banned_until

    for x in range(len(events_to_ban)):

        events_to_ban[x].is_banned = True

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

    #update events
    Events.objects.bulk_update(events_to_ban, ('is_banned',))

    #prepare users for update
    bulk_users = []

    for user_id in user_details:

        bulk_users.append(get_user_model()(
            pk=user_id,
            banned_until=user_details[user_id]['banned_until']
        ))

    #update users
    get_user_model().objects.bulk_update(bulk_users, ('banned_until',))


def cronjob_reset_replying_overdue():

    minimum_when_locked = get_datetime_now() - timedelta(seconds=settings.EVENT_ROOM_REPLY_EXPIRY_SECONDS)

    EventRooms.objects.filter(
        is_replying=True,
        locked_for_user__isnull=False,
        when_locked__lte=minimum_when_locked
    ).order_by(
        'when_locked'
    ).update(
        is_replying=None,
        locked_for_user=None,
        when_locked=None
    )[:settings.EVENT_ROOM_UNDO_REPLY_QUANTITY_PER_CRON]

