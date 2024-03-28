#py

#django
from django.contrib.auth import get_user_model
from django.db import connection
from django.db import transaction
from django.db.models import F, Q, Prefetch
from celery import shared_task
from django.core.cache import cache
from django.core.mail import send_mail

#apps
from voicewake.services import *
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
def task_send_otp_email(context:Literal['log_in', 'sign_up'], email:str, otp:str):

    #validate
    if (
        context not in ['log_in', 'sign_up'] or
        len(email) == 0 or
        len(otp) != settings.TOTP_NUMBER_OF_DIGITS
    ):

        raise custom_error(
            ValueError,
            __name__,
            dev_message="Invalid args."
        )

    email_subject = ''
    otp_title = ''

    if context == 'log_in':

        email_subject = "Code for login"
        otp_title = "Login code:"

    elif context == 'sign_up':

        email_subject = "Code for sign-up"
        otp_title = "Sign-up code:"

    #we can freely use math.ceil() as long as TOTP_TOLERANCE_S is sufficient
    otp_expiry_m = settings.TOTP_VALIDITY_S / 60
    otp_expiry_m = str(math.ceil(otp_expiry_m))

    email_message = get_template('email/otp.html').render(context={
        'otp_title': otp_title,
        'otp': otp,
        'otp_expiry': '%s minutes' % (otp_expiry_m),
    })

    send_mail(
        subject=email_subject,
        message='',
        html_message=email_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=True
    )


@shared_task
def task_normalisation(user_id:int, processing_cache_key:str, audio_clip_id:int, event_id:int):

    #validate
    if (
        len(processing_cache_key) == 0
    ):

        raise custom_error(
            ValueError,
            __name__,
            dev_message="Invalid args."
        )

    #get cache
    processing_cache = cache.get(processing_cache_key, None)

    if processing_cache is None:

        #cache must exist
        return

    if processing_cache['is_processing'] is True:

        #already processing
        return

    target_audio_clip = None
    target_event = None

    try:

        target_audio_clip = AudioClips.objects.get(pk=audio_clip_id)
        target_event = Events.objects.get(pk=event_id)

    except AudioClips.DoesNotExist:

        return

    except Events.DoesNotExist:

        return

    determined_processed_upload_key = CreateAudioClips.determine_processed_upload_key(
        unprocessed_upload_key=target_audio_clip.audio_file,
        unprocessed_file_extensions=settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS,
        processed_file_extension=os.environ['AUDIO_CLIP_PROCESSED_FILE_EXTENSION']
    )

    if determined_processed_upload_key == '':

        #already has processed extension
        raise custom_error(
            ValueError,
            __name__,
            dev_message=f'''
                Unexpected AudioClips.audio_file.
                AudioClips.id: {str(audio_clip_id)}
            '''
        )

    #call lambda
    #may take a while, so consider cronjobs and race conditions that may affect db rows

    #increment attempt early
    #to better prevent spam

    processing_cache['is_processing'] = True
    processing_cache['attempts_left'] -= 1

    #can't be bothered to properly -- the timeout
    cache.set(
        processing_cache_key,
        processing_cache,
        timeout=settings.AUDIO_CLIP_UNPROCESSED_EXPIRY_S
    )

    #refer to AWSLambdaNormaliseAudioClips.create_return_response()
    #when ok, will always return 200
    try:

        lambda_wrapper = AWSLambdaWrapper(
            is_ec2=settings.IS_EC2,
            timeout_s=int(os.environ['AWS_LAMBDA_NORMALISE_TIMEOUT_S']),
            region_name=os.environ['AWS_LAMBDA_REGION_NAME'],
            aws_access_key_id=os.environ['AWS_LAMBDA_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_LAMBDA_SECRET_ACCESS_KEY'],
        )

        lambda_wrapper.invoke_normalise_audio_clips_lambda(
            s3_region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_object_key=target_audio_clip.audio_file,
            processed_object_key=determined_processed_upload_key,
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            processed_bucket_name=os.environ['AWS_S3_MEDIA_BUCKET_NAME'],
        )

    except:

        #unexpected issues
        #if the cause is malicious file, will probably try again
        #next API call will evaluate max attempts at beginning, and respond accordingly
        raise custom_error(
            ValueError,
            __name__,
            dev_message='invoking lambda had unexpectedly failed',
            user_message='Something went wrong. Try again later.'
        )

    finally:

        #no longer processing
        processing_cache['is_processing'] = False
        cache.set(processing_cache_key, processing_cache)

    #validate lambda response

    target_audio_clip.refresh_from_db()
    target_event.refresh_from_db()

    serializer = AWSLambdaNormaliseAudioClipsAPISerializer(data=lambda_response_data, many=False)

    if (
        serializer.is_valid() is False or
        serializer.validated_data['lambda_status_code'] != 200
    ):

        serializer_error_message = get_serializer_error_message(serializer)

        if serializer_error_message != '':

            raise custom_error(
                ValueError,
                __name__,
                dev_message=serializer_error_message
            )

        #evaluate attempts again

        if processing_cache['attempts_left'] <= 0:

            #max attempts reached
            #set as "processing_max_attempts_reached", delete cache

            target_audio_clip.generic_status = GenericStatuses.objects.get(
                generic_status_name='processing_max_attempts_reached'
            )
            target_audio_clip.save()

            cache.delete(processing_cache_key)

        return

    #ok, proceed

    #check again
    if (
        target_audio_clip.generic_status.generic_status_name != 'processing' or
        target_event.generic_status.generic_status_name != 'processing'
    ):

        return

    #get data
    lambda_response_data = serializer.validated_data
    generic_status_ok = GenericStatuses.objects.get(generic_status_name='ok')
    datetime_now = get_datetime_now()

    #update audio clip

    #.update() and .filter().update() executes immediately
    #.update() returns rows affected, which we use to check for success
    AudioClips.objects.filter(
        pk=target_audio_clip.id,
        generic_status__generic_status_name='processing',
    ).update(
        audio_duration_s=lambda_response_data['audio_duration_s'],
        audio_volume_peaks=lambda_response_data['audio_volume_peaks'],
        audio_file=determined_processed_upload_key,
        generic_status=generic_status_ok,
        last_modified=datetime_now
    )

    #update event

    event_generic_status_name = ''

    if target_audio_clip.audio_clip_role.audio_clip_role_name == 'originator':

        event_generic_status_name = 'incomplete'

    elif target_audio_clip.audio_clip_role.audio_clip_role_name == 'responder':

        event_generic_status_name = 'completed'

    Events.objects.filter(
        pk=target_event.id,
        generic_status__generic_status_name='processing',
    ).update(
        generic_status=GenericStatuses.objects.get(generic_status_name=event_generic_status_name),
        last_modified=datetime_now
    )

    #delete queue, if any

    if target_audio_clip.audio_clip_role.audio_clip_role_name == 'responder':

        EventReplyQueues.objects.filter(
            event_id=target_event.id,
            locked_for_user_id=user_id
        ).delete()

    #delete lambda call record from cache on success
    cache.delete(processing_cache_key)
    processing_cache = None

    return


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

    when_locked_checkpoint = get_datetime_now() - timedelta(seconds=settings.EVENT_REPLY_MAX_DURATION_S)

    full_sql = '''
        WITH target_rows AS (
            SELECT erq.id FROM event_reply_queues AS erq
            WHERE erq.is_replying IS TRUE
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
def cronjob_handle_originator_processing_overdue():

    when_created_checkpoint = get_datetime_now() - timedelta(seconds=settings.AUDIO_CLIP_UNPROCESSED_EXPIRY_S)

    #set AudioClips to "deleted", then delete Events, and return AudioClips.id
    #we don't immediate delete AudioClips so that create/reply limit can be enforced
    #we delete cache via AudioClips.id
    full_sql = '''
        WITH
        target_audio_clips AS (
            SELECT ac.id, ac.event_id FROM audio_clips AS ac
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
            RETURNING tac.id, tac.event_id
        )
        DELETE FROM events AS e
        USING processing_overdue_audio_clips AS poac
        WHERE e.id = poac.event_id
        AND e.generic_status_id = (
            SELECT id FROM generic_statuses
            WHERE generic_status_name = %s
        )
        RETURNING poac.id
    '''

    full_params = [
        'originator',
        when_created_checkpoint,
        'processing',
        settings.CRONJOB_DEFAULT_ROW_LIMIT,
        'processing_overdue',
        'processing',
    ]

    target_cache_keys = []

    with connection.cursor() as cursor:

        cursor.execute(
            sql=full_sql,
            params=full_params,
        )

        #expect only AudioClips.id as (id,) tuple

        for row in cursor.fetchall():

            target_cache_keys.append(
                CreateAudioClips.determine_processing_cache_key(
                    audio_clip_id=row[0]
                )
            )

    #delete cache
    #cache content is irrelevant

    cache.delete_many(target_cache_keys)


@shared_task
def cronjob_handle_responder_processing_overdue():

    when_created_checkpoint = get_datetime_now() - timedelta(seconds=settings.AUDIO_CLIP_UNPROCESSED_EXPIRY_S)

    #delete AudioClips, reset Events to "incomplete", returns AudioClips.id
    #we don't directly delete AudioClips so that create/reply limit can be enforced
    #delete cache via AudioClips.id
    #do not touch EventReplyQueues
    full_sql = '''
        WITH
        target_audio_clips AS (
            SELECT ac.id, ac.event_id FROM audio_clips AS ac
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
            )
            FROM target_audio_clips AS tac
            WHERE ac.id = tac.id
            RETURNING tac.id, tac.event_id
        )
        UPDATE events AS e
        SET generic_status_id = (
            SELECT id FROM generic_statuses
            WHERE generic_status_name = %s
        )
        FROM processing_overdue_audio_clips AS poac
        WHERE e.id = poac.event_id
        AND e.generic_status_id = (
            SELECT id FROM generic_statuses
            WHERE generic_status_name = %s
        )
        RETURNING poac.id
    '''

    full_params = [
        'responder',
        when_created_checkpoint,
        'processing',
        settings.CRONJOB_DEFAULT_ROW_LIMIT,
        'processing_overdue',
        'incomplete',
        'processing',
    ]

    target_cache_keys = []

    with connection.cursor() as cursor:

        cursor.execute(
            sql=full_sql,
            params=full_params,
        )

        #expect only AudioClips.id as (id,) tuple

        for row in cursor.fetchall():

            target_cache_keys.append(
                CreateAudioClips.determine_processing_cache_key(
                    audio_clip_id=row[0]
                )
            )

    #delete cache
    #cache content is irrelevant

    cache.delete_many(target_cache_keys)


@shared_task
def cronjob_delete_audio_clip_processing_overdue():

    #here, truly delete from db
    #no longer need those "deleted" row to enforce latest create/reply limit
    #no need to involve AudioClipReports, as users cannot report when AudioClip isn't "ok"
    #no need to involve Events, as their relations are already handled

    passed_midnight_today = get_datetime_now().strftime('%Y-%m-%d 00:00:00.%f %z')

    full_sql = '''
        WITH
        target_audio_clips AS (
            SELECT ac.id, ac.event_id FROM audio_clips AS ac
            INNER JOIN generic_statuses AS gs ON gs.id = ac.generic_status_id
            INNER JOIN audio_clip_roles AS acr ON acr.id = ac.audio_clip_role_id
            AND ac.when_created <= %s
            AND gs.generic_status_name = %s
            ORDER BY ac.when_created ASC
            LIMIT %s
        )
        DELETE FROM audio_clips AS ac
        USING target_audio_clips AS tac
        WHERE ac.id = tac.id
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























