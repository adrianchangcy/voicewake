from django.contrib.auth import get_user_model
from django.db import connection
from django.db import transaction
from django.db.models import F, Q

#apps
from voicewake.services import *
from voicewake.models import *
from django.conf import settings


def cronjob_ban_audio_clips():

    datetime_now = get_datetime_now()

    #select via last_evaluated where it is >= earliest_datetime
    #which means we prioritise older last_evaluated
    #we may miss those that are < earliest_datetime,
    #but this also ensures that we don't eternally evaluate oldest reports
    earliest_datetime = datetime_now - timedelta(seconds=settings.BAN_AUDIO_CLIP_MIN_AGE_S)

    generic_statuses = GenericStatuses.objects.filter(generic_status_name__in=('deleted', 'incomplete',))
    generic_status_deleted = None
    generic_status_incomplete = None

    for row in generic_statuses:

        if row.generic_status_name == 'deleted':

            generic_status_deleted = row

        elif row.generic_status_name == 'incomplete':

            generic_status_incomplete = row

    with transaction.atomic():

        #get guaranteed bans and rows from related tables
        #Q() is important since you cannot do comparison with NULL, e.g. >= NULL
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
            Q(last_evaluated__isnull=True) | (Q(last_evaluated__gte=earliest_datetime) & Q(last_reported__gt=F('last_evaluated'))),
            audio_clip__is_banned=False,
            audio_clip__like_ratio__lte=settings.BAN_AUDIO_CLIP_LIKE_RATIO,
            audio_clip__dislike_count__gte=settings.BAN_AUDIO_CLIP_DISLIKE_COUNT,
        ).order_by(
            F('last_evaluated').asc(nulls_first=True)
        )[0:settings.CRONJOB_BAN_AUDIO_CLIP_QUANTITY_LIMIT]

        #evaluate and print
        print(str(len(audio_clip_reports)) + ' audio_clips to ban')

        events = []
        event_ids = []
        audio_clips = []
        users = []
        user_ids = []

        for index, audio_clip_report in enumerate(audio_clip_reports):

            #update audio_clip_reports to log evaluation

            audio_clip_reports[index].last_evaluated = datetime_now

            #update events for originators to be deleted, for responders will be incomplete
            #in cases where event reappears, deleted takes precedence

            if audio_clip_report.audio_clip.audio_clip_role.audio_clip_role_name == 'originator':

                #mark as deleted

                #remove event if added from responder
                if audio_clip_report.audio_clip.event.id in event_ids:

                    events.pop(event_ids.index(audio_clip_report.audio_clip.event.id))
                    event_ids.remove(audio_clip_report.audio_clip.event.id)

                #add event for update
                audio_clip_report.audio_clip.event.generic_status = generic_status_deleted
                events.append(audio_clip_report.audio_clip.event)
                event_ids.append(audio_clip_report.audio_clip.event.id)

            elif (
                audio_clip_report.audio_clip.audio_clip_role.audio_clip_role_name == 'responder' and
                audio_clip_report.audio_clip.event.generic_status.id != generic_status_deleted.id
            ):

                #mark as incomplete, do nothing if event has already been evaluated as originator

                if audio_clip_report.audio_clip.event.id not in event_ids:

                    #add event for update
                    audio_clip_report.audio_clip.event.generic_status = generic_status_incomplete
                    events.append(audio_clip_report.audio_clip.event)
                    event_ids.append(audio_clip_report.audio_clip.event.id)

            #update audio_clips to update is_banned=False and generic_status to 'deleted'

            audio_clip_report.audio_clip.is_banned = True
            audio_clip_report.audio_clip.last_modified = datetime_now
            audio_clip_report.audio_clip.generic_status = generic_status_deleted

            audio_clips.append(audio_clip_report.audio_clip)

            #update users to be banned

            if audio_clip_report.audio_clip.user.id not in user_ids:

                users.append(audio_clip_reports[index].audio_clip.user)
                user_ids.append(audio_clip_report.audio_clip.user.id)

            #use users and user_ids as source of truth for keeping track of ban_count

            target_user_index = user_ids.index(audio_clip_report.audio_clip.user.id)

            users[target_user_index].ban_count += 1
            ban_days = settings.CRONJOB_AUDIO_CLIP_BAN_DAYS ** users[target_user_index].ban_count

            #cap ban_days, else it can get out of hand
            if ban_days > settings.CRONJOB_AUDIO_CLIP_MAX_BAN_DAYS:

                ban_days = settings.CRONJOB_AUDIO_CLIP_MAX_BAN_DAYS

            users[target_user_index].banned_until = datetime_now + timedelta(days=ban_days)

        #update everything

        AudioClipReports.objects.bulk_update(audio_clip_reports, fields=('last_evaluated',))
        Events.objects.bulk_update(events, fields=('generic_status',))
        AudioClips.objects.bulk_update(audio_clips, fields=('is_banned', 'last_modified', 'generic_status',))
        get_user_model().objects.bulk_update(users, fields=('ban_count', 'banned_until',))


def cronjob_reset_event_reply_choice_overdue():

    when_locked_checkpoint = get_datetime_now() - timedelta(seconds=settings.EVENT_REPLY_CHOICE_MAX_DURATION_S)

    EventReplyQueues.objects.filter(
        when_locked__lte=when_locked_checkpoint,
        is_replying=False,
    ).order_by(
        'when_locked',
    ).delete()[0:settings.CRONJOB_UNDO_EVENT_REPLY_LIMIT]


def cronjob_reset_event_reply_overdue():

    when_locked_checkpoint = get_datetime_now() - timedelta(seconds=settings.EVENT_REPLY_MAX_DURATION_S)

    EventReplyQueues.objects.filter(
        when_locked__lte=when_locked_checkpoint,
        is_replying=True,
    ).order_by(
        'when_locked',
    ).delete()[0:settings.CRONJOB_UNDO_EVENT_REPLY_LIMIT]






