from django.contrib.auth import get_user_model
from django.db import connection
from django.db import transaction

#apps
from voicewake.services import *
from voicewake.models import *
from django.conf import settings


def cronjob_ban_audio_clips():

    #evaluate audio_clip_reports
    #to ban
        #set Events.generic_status.generic_status_name to 'deleted'
        #set AudioClips.generic_status.generic_status_name to 'deleted'
        #set AudioClips.is_banned to True

    #ensure not to select audio_clips that are too new
    maximum_when_created = get_datetime_now() - timedelta(seconds=settings.BAN_AUDIO_CLIP_AGE_SECONDS)

    #we delete reports of audio_clips that do not meet ban conditions
    with connection.cursor() as cursor:

        cursor.execute(
            '''
                WITH
                distinct_reported_audio_clips AS (
                    SELECT DISTINCT reported_audio_clip_id
                    FROM audio_clip_reports
                    ORDER BY reported_audio_clip_id ASC
                    LIMIT %s
                ),
                audio_clips_not_to_ban AS (
                    SELECT audio_clips.id
                    FROM audio_clips
                    INNER JOIN distinct_reported_audio_clips ON audio_clips.id = distinct_reported_audio_clips.reported_audio_clip_id
                    WHERE audio_clips.dislike_count < %s
                    OR (audio_clips.dislike_count::float / (audio_clips.like_count + audio_clips.dislike_count)) < %s
                    OR audio_clips.when_created > %s
                    OR audio_clips.is_banned IS TRUE
                )
                DELETE FROM audio_clip_reports AS er
                USING audio_clips_not_to_ban AS entb
                WHERE er.reported_audio_clip_id = entb.id
            ''',
            params=(
                settings.BAN_AUDIO_CLIP_QUANTITY_PER_CRON,
                settings.BAN_AUDIO_CLIP_DISLIKE_COUNT,
                settings.BAN_AUDIO_CLIP_DISLIKE_RATIO,
                maximum_when_created,
            )
        )

    #for audio_clips we are about to ban, we get count of those users' audio_clip_report_bans
    #this is to determine the  appropriate banned_until value

    #must cast any one column as float for the ratio to work
    #otherwise, since all of them are int, we'd get 0
    with transaction.atomic():

        audio_clips_to_ban = AudioClips.objects.prefetch_related(
            'user', 'audio_clip_role', 'event'
        ).select_for_update(
            of=('self', 'event')
        ).raw(
            '''
                WITH
                distinct_reported_audio_clips AS (
                    SELECT DISTINCT reported_audio_clip_id
                    FROM audio_clip_reports
                    ORDER BY reported_audio_clip_id ASC
                    LIMIT %s
                )
                SELECT audio_clips.*,
                (
                    SELECT COUNT(*) FROM audio_clips as audio_clips2
                    WHERE audio_clips2.user_id = audio_clips.user_id
                    AND audio_clips2.is_banned IS TRUE
                ) as ban_count
                FROM audio_clips
                RIGHT JOIN distinct_reported_audio_clips ON distinct_reported_audio_clips.reported_audio_clip_id = audio_clips.id
                WHERE audio_clips.dislike_count >= %s
                AND (audio_clips.dislike_count::float / (audio_clips.like_count + audio_clips.dislike_count)) >= %s
                AND audio_clips.when_created <= %s
                AND audio_clips.is_banned IS FALSE
            ''',
            params=(
                settings.BAN_AUDIO_CLIP_QUANTITY_PER_CRON,
                settings.BAN_AUDIO_CLIP_DISLIKE_COUNT,
                settings.BAN_AUDIO_CLIP_DISLIKE_RATIO,
                maximum_when_created,
            )
        )

        print(str(len(audio_clips_to_ban)) + ' audio_clips to ban')

        #ban
        #we will likely get multiple audio_clips from the same user here
        #to accurately set banned_until on a per-audio_clip basis, we track and update ban_count here

        datetime_now = get_datetime_now()
        user_details = {}   #keeps track of ban_count and banned_until

        event_ids = []
        bulk_events = []
        generic_status_deleted = GenericStatuses.objects.get(generic_status_name='deleted')
        generic_status_incomplete = GenericStatuses.objects.get(generic_status_name='incomplete')

        for x in range(len(audio_clips_to_ban)):

            audio_clips_to_ban[x].is_banned = True
            audio_clips_to_ban[x].generic_status = generic_status_deleted

            #track user and ban_count for cases of multiple audio_clips retrieved with same user
            user_id = audio_clips_to_ban[x].user.id

            if user_id in user_details:

                banned_until = datetime_now + timedelta(days=(
                    settings.BAN_AUDIO_CLIP_DURATION_PER_BAN_DAYS * user_details[user_id]['ban_count']
                ))

                user_details[user_id]['ban_count'] = user_details[user_id]['ban_count'] + 1
                user_details[user_id]['banned_until'] = banned_until

            else:

                banned_until = datetime_now + timedelta(days=(
                    settings.BAN_AUDIO_CLIP_DURATION_PER_BAN_DAYS * audio_clips_to_ban[x].ban_count
                ))

                user_details[user_id] = {
                    'ban_count': audio_clips_to_ban[x].ban_count + 1,
                    'banned_until': banned_until
                }

            current_audio_clip_role_name = audio_clips_to_ban[x].audio_clip_role.audio_clip_role_name
            expected_generic_status = None

            if current_audio_clip_role_name == 'originator':

                expected_generic_status = generic_status_deleted

            elif current_audio_clip_role_name == 'responder':

                expected_generic_status = generic_status_incomplete

            else:

                raise ValueError('Error when evaluating audio_clip_role_name.')

            #prepare to handle event
            #on edge case where event can be both deleted/incomplete, deleted takes precedence
            event_id = audio_clips_to_ban[x].event.id

            if event_id not in event_ids:

                event_ids.append(event_id)

                bulk_events.append(Events(
                    pk=event_id,
                    generic_status=expected_generic_status,
                    when_locked=None,
                    is_replying=None,
                    locked_for_user=None
                ))

            elif (
                current_audio_clip_role_name == 'originator' and
                bulk_events[event_ids.index(event_id)].generic_status != generic_status_deleted
            ):

                #ensure deleted takes precedence over incomplete
                bulk_events[event_ids.index(event_id)].generic_status = generic_status_deleted

        #update audio_clips
        AudioClips.objects.bulk_update(audio_clips_to_ban, ('is_banned', 'generic_status',))

        #update events
        Events.objects.bulk_update(bulk_events, ('generic_status', 'when_locked', 'is_replying', 'locked_for_user',))

    #prepare users for update
    bulk_users = []

    for user_id in user_details:

        bulk_users.append(get_user_model()(
            pk=user_id,
            banned_until=user_details[user_id]['banned_until']
        ))

    #update users
    get_user_model().objects.bulk_update(bulk_users, ('banned_until',))

    #delete audio_clip_reports
    AudioClipReports.objects.filter(reported_audio_clip__in=audio_clips_to_ban).delete()


def cronjob_reset_reply_choice_overdue():

    #have this to reduce the chances of cronjob + auto-cancel reply from frontend colliding
    #which would be fine, but it's better for UX
    extra_seconds = 60

    max_when_locked = get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_CHOICE_EXPIRY_SECONDS + extra_seconds))

    with connection.cursor() as cursor:

        cursor.execute(
            '''
            WITH selected_events AS (
                SELECT * FROM events
                WHERE is_replying IS FALSE
                AND locked_for_user_id IS NOT NULL
                AND when_locked <= %s
                LIMIT %s
            )
            UPDATE events
            SET is_replying = NULL, locked_for_user_id = NULL, when_locked = NULL
            FROM selected_events
            WHERE events.id = selected_events.id
            ''',
            params=(
                max_when_locked,
                settings.EVENT_UNDO_REPLY_QUANTITY_PER_CRON,
            )
        )


def cronjob_reset_replying_overdue():

    #have this to reduce the chances of cronjob + auto-cancel reply from frontend colliding
    #which would be fine, but it's better for UX
    extra_seconds = 60

    max_when_locked = get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_EXPIRY_SECONDS + extra_seconds))

    with connection.cursor() as cursor:

        cursor.execute(
            '''
            WITH selected_events AS (
                SELECT * FROM events
                WHERE is_replying IS TRUE
                AND locked_for_user_id IS NOT NULL
                AND when_locked <= %s
                LIMIT %s
            )
            UPDATE events
            SET is_replying = NULL, locked_for_user_id = NULL, when_locked = NULL
            FROM selected_events
            WHERE events.id = selected_events.id
            ''',
            params=(
                max_when_locked,
                settings.EVENT_UNDO_REPLY_QUANTITY_PER_CRON,
            )
        )






