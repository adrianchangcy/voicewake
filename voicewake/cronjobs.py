#py
from datetime import datetime, timezone, timedelta, tzinfo
import math
from typing import Union
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
from typing import Literal
from urllib.parse import quote, unquote
import sys

#django
from django.contrib.auth import get_user_model
from django.db import connection
from django.db import transaction
from django.db.models import F, Q, Prefetch
from celery import shared_task
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import get_template

#apps
from voicewake.services import *
from voicewake.serializers import AWSLambdaNormaliseAudioClipsAPISerializer
from voicewake.models import *
from django.conf import settings



#tight coupling between event_reply_queue and normalising/processing audio clips
    #easier to maintain/manage when all share the same timeframe
    #drawback is that when time is nearly up, most likely no chance for reupload
        #just increase reply duration
    #tried and failed alternative:
        #keep processing separate, i.e. only delete queue first
        #was to allow users more time to process
        #but this "time is nearly up" is unavoidable, even for this context
#deletion
    #deletion via raw query
        #only used if affected table has no signal to send, and has no FK
        #can control row quantity, whereas queryset just deletes everything
            #tested: delete() returns deleted tuples first (i.e. all), and applying [0:1] just filters them
        #can guarantee not loaded into memory
        #queryset delete() "is subject to change"
    #avoiding Django cascade behaviour when deleting
        #Django emulates cascade at ORM-level
            #this is to send signals, etc.
            #however, this can consume a lot of memory as it scales

#1-to-1 cases
    #commonly the case, i.e. update 1 event based on 1 originator/responder
    #if this changes in the future, be sure to check whether RETURNING behaves expectedly
        #i.e. select 2 AudioClips, affect 1 Events, RETURNING info from 2 AudioClips



@shared_task
def cronjob_prepare_celery_beat_healthcheck(cache_timeout=60):

    #no easy way to healthcheck celery beat itself
    #so we set key-value at Redis with expiry of 2 minutes
    #then for healthcheck, we check whether key exists
    #be sure to delay healthcheck at Docker for this task's first time
    #https://github.com/celery/celery/issues/3694#issuecomment-481114772

    #set cache key with timeout
    cache.set(settings.CELERY_BEAT_HEALTHCHECK_CACHE_KEY, 0, timeout=cache_timeout)


@shared_task
def cronjob_ban_audio_clips():

    #select via last_evaluated where it is >= earliest_datetime
    #which means we prioritise older last_evaluated
    #we may miss those that are < earliest_datetime,
    #but this also ensures that we don't eternally evaluate oldest reports

    datetime_now = get_datetime_now()

    earliest_datetime = datetime_now - timedelta(seconds=settings.BAN_AUDIO_CLIP_MIN_AGE_S)

    generic_status_deleted = GenericStatuses.objects.get(generic_status_name='deleted')
    generic_status_incomplete = GenericStatuses.objects.get(generic_status_name='incomplete')

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
            'audio_clip__event__generic_status',
            'audio_clip__audio_clip_role',
            'audio_clip__user',
        ).filter(
            (
                Q(last_evaluated__isnull=True) |
                (
                    Q(last_evaluated__gte=earliest_datetime) &
                    Q(last_reported__gt=F('last_evaluated'))
                )
            ),
            audio_clip__generic_status__generic_status_name='ok',
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
                #we prioritise "deleted" over "incomplete" for event
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

        AudioClipReports.objects.bulk_update(
            audio_clip_reports,
            fields=('last_evaluated',),
            batch_size=100,
        )

        Events.objects.bulk_update(
            events,
            fields=('generic_status',),
            batch_size=100,
        )

        AudioClips.objects.bulk_update(
            audio_clips,
            fields=('is_banned', 'last_modified', 'generic_status',),
            batch_size=100,
        )

        get_user_model().objects.bulk_update(
            users,
            fields=('ban_count', 'banned_until',),
            batch_size=100,
        )


@shared_task
def cronjob_handle_originator_processing_overdue():

    when_created_checkpoint = get_datetime_now() - timedelta(seconds=settings.AUDIO_CLIP_UNPROCESSED_EXPIRY_S)

    #set AudioClips to "processing_overdue", then delete Events, and return AudioClips.id
    #don't immediate delete AudioClips so that create/reply limit can be enforced
    #delete cache
    full_sql = '''
        WITH
        target_audio_clips AS (
            SELECT ac.id, ac.event_id, ac.user_id FROM audio_clips AS ac
            INNER JOIN generic_statuses AS gs ON gs.id = ac.generic_status_id
            INNER JOIN audio_clip_roles AS acr ON acr.id = ac.audio_clip_role_id
            WHERE acr.audio_clip_role_name = %s
            AND ac.when_created <= %s
            AND gs.generic_status_name = %s
            ORDER BY ac.when_created ASC
            LIMIT %s
        ),
        processing_overdue_audio_clips AS (
            UPDATE audio_clips AS ac
            SET generic_status_id = (
                SELECT id FROM generic_statuses
                WHERE generic_status_name = %s
            ),
            event_id = NULL
            FROM target_audio_clips AS tac
            WHERE ac.id = tac.id
            RETURNING tac.id, tac.event_id, tac.user_id
        )
        DELETE FROM events AS e
        USING processing_overdue_audio_clips AS poac
        WHERE e.id = poac.event_id
        AND e.generic_status_id = (
            SELECT id FROM generic_statuses
            WHERE generic_status_name = %s
        )
        RETURNING poac.id, poac.user_id
    '''

    full_params = [
        'originator',
        when_created_checkpoint,
        'processing',
        settings.CRONJOB_DEFAULT_ROW_LIMIT,
        'processing_overdue',
        'processing',
    ]

    with connection.cursor() as cursor:

        cursor.execute(
            sql=full_sql,
            params=full_params,
        )

        #expect tuple based on last RETURNING
        cursor_rows = cursor.fetchall()

        datetime_now = get_datetime_now()

        processing_cache_keys = []

        #prepare cache keys first, so we can use cache.get_many()

        for row in cursor_rows:

            audio_clip_id, user_id = row

            #if processing_cache for this user already exists in this cronjob, use it

            processing_cache_key = CreateAudioClips.determine_processing_cache_key(user_id=user_id)

            if processing_cache_key not in processing_cache_keys:

                processing_cache_keys.append(processing_cache_key)

        #get caches

        processing_caches = cache.get_many(processing_cache_keys)

        #remove processings

        for row in cursor_rows:

            audio_clip_id, user_id = row

            processing_cache_key = CreateAudioClips.determine_processing_cache_key(user_id=user_id)

            if processing_cache_key in processing_cache_keys:

                processing_caches[processing_cache_key]['processings'].pop(str(audio_clip_id))
                processing_caches[processing_cache_key]['last_updated'] = datetime_now

        #save

        cache.set_many(processing_caches)


@shared_task
def cronjob_delete_event_reply_queue_not_replying_overdue():

    when_locked_checkpoint = get_datetime_now() - timedelta(seconds=settings.EVENT_REPLY_CHOICE_MAX_DURATION_S)

    full_sql = '''
        WITH target_rows AS (
            SELECT erq.id FROM event_reply_queues AS erq
            WHERE erq.is_replying IS FALSE
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
        when_locked_checkpoint,
        settings.CRONJOB_DEFAULT_ROW_LIMIT,
    ]

    with connection.cursor() as cursor:

        cursor.execute(
            sql=full_sql,
            params=full_params,
        )


@shared_task
def cronjob_delete_event_reply_queue_is_replying_overdue():

    #deleted event reply queues that are replying, update audio clip
    #audio clip is updated, instead of deleted, to enforce reply limit
    #delete cache

    when_locked_checkpoint = get_datetime_now() - timedelta(seconds=settings.EVENT_REPLY_MAX_DURATION_S)

    full_sql = '''
        WITH
        target_event_reply_queues AS (
            SELECT erq.id, erq.locked_for_user_id, erq.event_id
            FROM event_reply_queues AS erq
            WHERE erq.is_replying IS TRUE
            AND erq.when_locked <= %s
            ORDER BY when_locked ASC
            LIMIT %s
        ),
        deleted_event_reply_queues AS (
            DELETE FROM event_reply_queues AS erq
            USING target_event_reply_queues as terq
            WHERE erq.id = terq.id
            RETURNING terq.locked_for_user_id, terq.event_id
        )
        UPDATE audio_clips AS ac
        SET generic_status_id = (
            SELECT id FROM generic_statuses AS gs
            WHERE gs.generic_status_name = %s
        )
        FROM deleted_event_reply_queues AS derq
        WHERE ac.user_id = derq.locked_for_user_id
        AND ac.event_id = derq.event_id
        RETURNING ac.id, ac.user_id
        ;
    '''

    full_params = [
        when_locked_checkpoint,
        settings.CRONJOB_DEFAULT_ROW_LIMIT,
        'processing_overdue',
    ]

    with connection.cursor() as cursor:

        cursor.execute(
            sql=full_sql,
            params=full_params,
        )

        #expect tuple based on last RETURNING
        cursor_rows = cursor.fetchall()

        datetime_now = get_datetime_now()

        processing_cache_keys = []

        #prepare cache keys first, so we can use cache.get_many()

        for row in cursor_rows:

            audio_clip_id, user_id = row

            #if processing_cache for this user already exists in this cronjob, use it

            processing_cache_key = CreateAudioClips.determine_processing_cache_key(user_id=user_id)

            if processing_cache_key not in processing_cache_keys:

                processing_cache_keys.append(processing_cache_key)

        #get caches

        processing_caches = cache.get_many(processing_cache_keys)

        #remove processings

        for row in cursor_rows:

            audio_clip_id, user_id = row

            processing_cache_key = CreateAudioClips.determine_processing_cache_key(user_id=user_id)

            if processing_cache_key in processing_caches:

                processing_caches[processing_cache_key]['processings'].pop(str(audio_clip_id))
                processing_caches[processing_cache_key]['last_updated'] = datetime_now

        #save

        cache.set_many(processing_caches)


@shared_task
def cronjob_delete_audio_clip_processing_overdue():

    #here, truly delete from db
    #no longer need those "deleted" row to enforce latest create/reply limit
    #no need to involve AudioClipReports, as users cannot report when AudioClip isn't "ok"
    #no need to involve Events, as their relations are already handled beforehand

    passed_midnight_today = get_datetime_now().strftime('%Y-%m-%d 00:00:00.%f %z')

    #delete AudioClips

    full_sql = '''
        WITH
        target_audio_clips AS (
            SELECT ac.id FROM audio_clips AS ac
            INNER JOIN generic_statuses AS gs ON gs.id = ac.generic_status_id
            INNER JOIN audio_clip_roles AS acr ON acr.id = ac.audio_clip_role_id
            AND ac.when_created <= %s
            AND gs.generic_status_name = %s
            ORDER BY ac.when_created ASC
            LIMIT %s
        )
        SELECT tac.id FROM target_audio_clips AS tac
        ;
    '''

    full_params = [
        passed_midnight_today,
        'processing_overdue',
        settings.CRONJOB_DEFAULT_ROW_LIMIT,
    ]

    with connection.cursor() as cursor:

        cursor.execute(
            sql=full_sql,
            params=full_params,
        )

        #delete all child relations

        cursor_rows = cursor.fetchall()

        audio_clip_ids = []

        for row in cursor_rows:

            (audio_clip_id,) = row
            audio_clip_ids.append(audio_clip_id)

        AudioClipLikesDislikes.objects.filter(audio_clip_id__in=audio_clip_ids).delete()
        AudioClips.objects.filter(pk__in=audio_clip_ids).delete()
























