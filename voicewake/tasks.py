from django.contrib.auth import get_user_model
from django.db import connection
from django.db import transaction
from django.db.models import F, Q
from celery import shared_task

#apps
from voicewake.services import *
from voicewake.models import *
from django.conf import settings


@shared_task
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


@shared_task
def cronjob_delete_event_reply_choice_overdue():

    when_locked_checkpoint = get_datetime_now() - timedelta(seconds=settings.EVENT_REPLY_CHOICE_MAX_DURATION_S)

    EventReplyQueues.objects.filter(
        when_locked__lte=when_locked_checkpoint,
        is_replying=False,
    ).order_by(
        'when_locked',
    ).delete()[0:settings.CRONJOB_DEFAULT_ROW_LIMIT]


@shared_task
def cronjob_delete_event_reply_overdue():

    #delete only those that does not have AudioClips

    when_locked_checkpoint = get_datetime_now() - timedelta(seconds=settings.EVENT_REPLY_CHOICE_MAX_DURATION_S)

    full_sql = '''
        WITH target_rows AS (
            SELECT erq.id FROM event_reply_queues AS erq
            LEFT JOIN audio_clips AS ac ON erq.event_id = ac.event_id
                AND ac.audio_clip_role_id = (
                    SELECT acr.id FROM audio_clip_roles AS acr
                    WHERE acr.audio_clip_role_name = %s
                )
            WHERE erq.is_replying IS TRUE
            AND ac.id IS NULL
            AND erq.when_locked <= %s
            ORDER BY when_locked ASC
            LIMIT %s
        )
        DELETE FROM event_reply_queues AS erq
        USING target_rows as tr
        WHERE erq.id = tr.id
        ;
    '''

    full_params = [
        'responder',
        when_locked_checkpoint,
        settings.CRONJOB_DEFAULT_ROW_LIMIT,
    ]

    EventReplyQueues.objects.raw(
        raw_query=full_sql,
        params=full_params
    )


@shared_task
def cronjob_delete_originator_processing_overdue():

    #delete only Events.GenericStatuses.generic_status_name='processing'
    #as long as AudioClips.event_id FK has delete on CASCADE

    when_created_checkpoint = get_datetime_now() - timedelta(seconds=settings.AUDIO_CLIP_UNPROCESSED_EXPIRY_S)

    Events.objects.filter(
        when_created__lte=when_created_checkpoint,
        generic_status__generic_status_name='processing',
    ).order_by(
        'when_created',
    ).delete()[0:settings.CRONJOB_DEFAULT_ROW_LIMIT]


@shared_task
def cronjob_delete_responder_processing_overdue():

    #delete from AudioClips first
    #EventReplyQueues naturally has less rows, so less expensive when sequential scan is used

    when_created_checkpoint = get_datetime_now() - timedelta(seconds=settings.AUDIO_CLIP_UNPROCESSED_EXPIRY_S)

    full_sql = '''
        WITH
        target_audio_clips AS (
            SELECT ac.id FROM audio_clips AS ac
            INNER JOIN audio_clip_roles AS acr ON ac.audio_clip_role_id = acr.id
            INNER JOIN generic_statuses AS gs ON ac.generic_status_id = gs.id
            WHERE acr.audio_clip_role_name = %s
            AND gs.generic_status_name = %s
            AND ac.when_created <= %s
            ORDER BY ac.when_created ASC
            LIMIT %s
        ),
        deleted_audio_clips AS (
            DELETE FROM audio_clips AS ac
            USING target_audio_clips as tac
            WHERE ac.id = tac.id
            RETURNING ac.event_id
        )
        DELETE FROM event_reply_queues AS erq
        USING deleted_audio_clips AS dac
        WHERE erq.event_id = dac.event_id
        ;
    '''

    full_params = [
        'responder',
        'processing',
        when_created_checkpoint,
        settings.CRONJOB_DEFAULT_ROW_LIMIT
    ]

    EventReplyQueues.objects.raw(
        raw_query=full_sql,
        params=full_params
    )