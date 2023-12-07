from django.contrib.auth import get_user_model
from django.db import connection
from django.db import transaction
from django.db.models import F

#apps
from voicewake.services import *
from voicewake.models import *
from django.conf import settings


def cronjob_ban_audio_clips():

    datetime_now = get_datetime_now()

    #ensure not to select audio_clips that are too new
    earliest_datetime = datetime_now - timedelta(seconds=settings.BAN_AUDIO_CLIP_AGE_SECONDS)

    generic_status_deleted = GenericStatuses.objects.get(generic_status_name='deleted')

    with transaction.atomic():

        #get guaranteed bans and rows from related tables
        audio_clip_reports = AudioClipReports.objects.select_for_update(
            of=('self', 'audio_clip',),
            no_key=True,
        ).select_related(
            'audio_clip',
        ).prefetch_related(
            'audio_clip__event',
            'audio_clip__audio_clip_role',
            'audio_clip__user',
        ).filter(
            audio_clip__is_banned=False,
            audio_clip__like_ratio__lte=settings.BAN_AUDIO_CLIP_LIKE_RATIO,
            audio_clip__dislike_count__gte=settings.BAN_AUDIO_CLIP_DISLIKE_COUNT,
            last_evaluated__gte=earliest_datetime,
            last_reported__gt=F('last_evaluated'),
        ).order_by(
            F('last_evaluated').asc(nulls_first=True)
        )[0:settings.BAN_AUDIO_CLIP_QUANTITY_CRONJOB_LIMIT]

        #evaluate and print
        print(str(len(audio_clip_reports)) + ' audio_clips to ban')

        events = []
        audio_clips = []
        users = []
        user_ids = []

        for index, audio_clip_report in enumerate(audio_clip_reports):

            #update audio_clip_reports to log evaluation

            audio_clip_reports[index].last_evaluated = datetime_now

            #update events for originators to be deleted

            if audio_clip_report.audio_clip.audio_clip_role.audio_clip_role_name == 'originator':

                audio_clip_report.audio_clip.event.generic_status = generic_status_deleted

                events.append(audio_clip_report.audio_clip.event.generic_status)

            #update audio_clips to update is_banned=False and generic_status to 'deleted'

            audio_clip_report.audio_clip.is_banned = True
            audio_clip_report.audio_clip.last_modified = datetime_now
            audio_clip_report.audio_clip.generic_status = generic_status_deleted

            audio_clips.append(audio_clip_report.audio_clip)

            #update users to be banned

            #use index to reference original list because we want to keep track of ban_count
            audio_clip_reports[index].audio_clip.user.ban_count += 1
            audio_clip_reports[index].audio_clip.user.banned_until = (
                settings.BAN_AUDIO_CLIP_DURATION_PER_BAN_DAYS ** audio_clip_reports[index].audio_clip.user.ban_count
            )

            if audio_clip_report.audio_clip.user.id not in user_ids:

                users.append(audio_clip_reports[index].audio_clip.user)
                user_ids.append(audio_clip_report.audio_clip.user.id)

            else:

                users[user_ids.index(audio_clip_report.audio_clip.user.id)] = audio_clip_reports[index].audio_clip.user

        #update everything

        AudioClipReports.objects.bulk_update(audio_clip_reports, fields=('last_evaluated',))
        Events.objects.bulk_update(events, fields=('generic_status',))
        AudioClips.objects.bulk_update(audio_clips, fields=('is_banned', 'last_modified', 'generic_status',))
        get_user_model().objects.bulk_update(users, fields=('ban_count', 'banned_until',))



def cronjob_reset_event_reply_choice_overdue():

    #have this to reduce the chances of cronjob + auto-cancel reply from frontend colliding
    #which would be fine, but it's better for UX
    extra_seconds = 60

    earliest_when_locked = get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_CHOICE_EXPIRY_SECONDS + extra_seconds))

    EventReplyQueues.objects.filter(
        when_locked__gte=earliest_when_locked,
        is_replying=False,
    ).order_by(
        'when_locked',
    ).delete()[0:settings.EVENT_UNDO_REPLY_QUANTITY_CRONJOB_LIMIT]



def cronjob_reset_event_reply_overdue():

    #have this to reduce the chances of cronjob + auto-cancel reply from frontend colliding
    #which would be fine, but it's better for UX
    extra_seconds = 60

    earliest_when_locked = get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_EXPIRY_SECONDS + extra_seconds))

    EventReplyQueues.objects.filter(
        when_locked__gte=earliest_when_locked,
        is_replying=True,
    ).order_by(
        'when_locked',
    ).delete()[0:settings.EVENT_UNDO_REPLY_QUANTITY_CRONJOB_LIMIT]






