#py
from datetime import datetime, timezone, timedelta, tzinfo
import math
from typing import Union
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
from typing import Literal
from urllib.parse import quote, unquote
from django.db import connection

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

    #for subject, initially was simply "Code for x"
    #but Gmail stacks emails with the same subject together
    #if the entire stack is never opened, Gmail uses older email as stack summary, which is bad

    email_subject = ''
    otp_title = ''

    if context == 'log_in':

        email_subject = "Login code: %s" % (otp)
        otp_title = "Login code:"

    elif context == 'sign_up':

        email_subject = "Sign-up code: %s" % (otp)
        otp_title = "Sign-up code:"

    email_message = get_template('email/otp.html').render(context={
        'otp_title': otp_title,
        'otp': otp,
        'otp_expiry': get_pretty_datetime(settings.TOTP_VALIDITY_S),
    })

    send_mail(
        subject=email_subject,
        message='',
        html_message=email_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False
    )


#will validate and invalidate
#must be able to invalidate, since task can potentially start much later than when originally called
#db is source of truth for backend (i.e. here), while cache is source of truth for frontend
@shared_task
def task_normalisation(user_id:int, processing_cache_key:str, audio_clip_id:int, event_id:int):

    target_audio_clip = None
    target_event = None
    target_event_reply_queue = None

    try:

        target_audio_clip = AudioClips.objects.select_related(
            'audio_clip_role',
            'generic_status',
        ).get(pk=audio_clip_id)

        target_event = Events.objects.select_related(
            'generic_status',
        ).get(pk=event_id)

        if target_audio_clip.audio_clip_role.audio_clip_role_name == 'responder':

            target_event_reply_queue = EventReplyQueues.objects.get(
                locked_for_user_id=user_id,
                event_id=event_id
            )

    except AudioClips.DoesNotExist:

        raise custom_error(
            ValueError,
            __name__,
            dev_message="AudioClips.DoesNotExist"
        )

    except Events.DoesNotExist:

        raise custom_error(
            ValueError,
            __name__,
            dev_message="Events.DoesNotExist"
        )

    except EventReplyQueues.DoesNotExist:

        raise custom_error(
            ValueError,
            __name__,
            dev_message="EventReplyQueues.DoesNotExist"
        )

    #prepare cache

    processing_cache = CreateAudioClips.get_or_create_processing_cache(user_id)

    #check db if can normalise

    db_check_before_normalise = CreateAudioClips.check_db_for_normalisation_context(
        audio_clip=target_audio_clip,
        event=target_event,
        event_reply_queue=target_event_reply_queue
    )

    if db_check_before_normalise['is_audio_clip_processing'] is True:

        raise custom_error(
            ValueError,
            __name__,
            dev_message="Already processing."
        )

    if db_check_before_normalise['do_rows_match_context'] is False:

        #remove any processing from cache

        if str(audio_clip_id) in processing_cache['processings']:

            processing_cache['processings'].pop(str(audio_clip_id))

            CreateAudioClips.set_processing_cache(
                processing_cache_key=processing_cache_key,
                processing_cache=processing_cache
            )

        raise custom_error(
            ValueError,
            __name__,
            dev_message="Can no longer normalise."
        )

    #since can normalise, ensure processing object exists

    processing_cache = CreateAudioClips.ensure_processing_object_exists_in_processing_cache(
        processing_cache_key=processing_cache_key,
        processing_cache=processing_cache,
        event=target_event,
        audio_clip=target_audio_clip,
        set_cache=True,
    )

    #just confirm audio_file is fine in db

    determined_processed_upload_key = CreateAudioClips.determine_processed_upload_key(
        unprocessed_upload_key=target_audio_clip.audio_file,
        unprocessed_file_extensions=settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS,
        processed_file_extension=settings.AUDIO_CLIP_PROCESSED_FILE_EXTENSION
    )

    if determined_processed_upload_key == '':

        #already has processed extension
        raise custom_error(
            ValueError,
            __name__,
            dev_message=f'''
                AudioClips.audio_file already has processed extension.
                AudioClips.id: {str(audio_clip_id)}
            '''
        )

    #update db
    if target_audio_clip.generic_status.generic_status_name in ['processing_pending', 'processing_failed']:

        target_audio_clip.generic_status = GenericStatuses.objects.get(generic_status_name='processing')
        target_audio_clip.save()

    #update attempt at cache early to better prevent spam

    processing_cache['processings'][str(audio_clip_id)]['status'] = 'processing'
    processing_cache['processings'][str(audio_clip_id)]['attempts_left'] -= 1

    CreateAudioClips.set_processing_cache(
        processing_cache_key=processing_cache_key,
        processing_cache=processing_cache
    )

    #to maintain attempt accuracy if redis suddenly goes down, we preserve the object
    processing_object = processing_cache['processings'][str(audio_clip_id)]

    #call lambda
    #may take a while, so consider cronjobs and race conditions that may affect db rows

    lambda_response_data = None

    #refer to AWSLambdaNormaliseAudioClips.create_return_response()
    #when ok, will always return 200
    try:

        lambda_wrapper = AWSLambdaWrapper(
            is_ec2=settings.IS_EC2,
            timeout_s=settings.AWS_LAMBDA_NORMALISE_TIMEOUT_S,
            region_name=os.environ['AWS_LAMBDA_REGION_NAME'],
            aws_access_key_id=os.environ['AWS_LAMBDA_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_LAMBDA_SECRET_ACCESS_KEY'],
        )

        lambda_response_data = lambda_wrapper.invoke_normalise_audio_clips_lambda(
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
            dev_message='Invoking lambda had unexpectedly failed.',
            user_message='Something went wrong. Try again later.'
        )

    #refetch rows from db to mitigate race condition
    #db will raise DoesNotExist if they've been deleted

    try:

        target_audio_clip.refresh_from_db()

        target_event.refresh_from_db()

        if target_event_reply_queue is not None:

            target_event_reply_queue.refresh_from_db()

    except AudioClips.DoesNotExist:

        raise custom_error(
            ValueError,
            __name__,
            dev_message="AudioClips.DoesNotExist"
        )

    except Events.DoesNotExist:

        raise custom_error(
            ValueError,
            __name__,
            dev_message="Events.DoesNotExist"
        )

    except EventReplyQueues.DoesNotExist:

        raise custom_error(
            ValueError,
            __name__,
            dev_message="EventReplyQueues.DoesNotExist"
        )

    #no need to check db if can normalise again
    #there should be no normal logic that can turn it from True to False while audio_clip is still 'processing'

    #refetch cache to mitigate race condition
    #intentionally done after the queries above for sake of mitigation

    processing_cache = CreateAudioClips.get_or_create_processing_cache(user_id)

    #reuse processing_object from above for best accuracy
    #ensure it exists in refetched cache

    if str(audio_clip_id) in processing_cache['processings']:

        processing_cache['processings'].update({
            str(audio_clip_id): processing_object
        })

    else:

        processing_cache['processings'][str(audio_clip_id)] = processing_object

    #validate db again

    db_check_before_normalise = CreateAudioClips.check_db_for_normalisation_context(
        audio_clip=target_audio_clip,
        event=target_event,
        event_reply_queue=target_event_reply_queue
    )

    if db_check_before_normalise['is_audio_clip_processing'] is False:

        raise custom_error(
            ValueError,
            __name__,
            dev_message="Expected to be processing."
        )

    if db_check_before_normalise['do_rows_match_context'] is False:

        #remove any processing from cache

        if str(audio_clip_id) in processing_cache['processings']:

            processing_cache['processings'].pop(str(audio_clip_id))

            CreateAudioClips.set_processing_cache(
                processing_cache_key=processing_cache_key,
                processing_cache=processing_cache
            )

        raise custom_error(
            ValueError,
            __name__,
            dev_message="Can no longer normalise."
        )

    #validate lambda response

    serializer = AWSLambdaNormaliseAudioClipsAPISerializer(data=lambda_response_data, many=False)

    #handle lambda failure

    if (
        serializer.is_valid() is False or
        serializer.validated_data['lambda_status_code'] != 200
    ):

        #can reattempt
        if processing_cache['processings'][str(audio_clip_id)]['attempts_left'] > 0:

            processing_cache['processings'][str(audio_clip_id)]['status'] = 'processing_failed'

            CreateAudioClips.set_processing_cache(
                processing_cache_key,
                processing_cache
            )

            target_audio_clip.generic_status = GenericStatuses.objects.get(
                generic_status_name='processing_failed'
            )
            target_audio_clip.save()

            return

        #max attempts reached

        #update cache

        processing_cache['processings'].pop(str(audio_clip_id))

        CreateAudioClips.set_processing_cache(
            processing_cache_key=processing_cache_key,
            processing_cache=processing_cache
        )

        #update audio clip

        if target_audio_clip.generic_status.generic_status_name == 'processing':

            target_audio_clip.generic_status = GenericStatuses.objects.get(
                generic_status_name='processing_max_attempts_reached'
            )
            target_audio_clip.save()

        #update event

        if target_event.generic_status.generic_status_name in ['processing', 'incomplete']:

            event_generic_status_name = ''

            if target_audio_clip.audio_clip_role.audio_clip_role_name == 'originator':

                event_generic_status_name = 'deleted'

            elif target_audio_clip.audio_clip_role.audio_clip_role_name == 'responder':

                event_generic_status_name = 'incomplete'

            target_event.generic_status = GenericStatuses.objects.get(
                generic_status_name=event_generic_status_name
            )
            target_event.save()

        #delete queue for responder

        if target_audio_clip.audio_clip_role.audio_clip_role_name == 'responder':

            EventReplyQueues.objects.filter(
                pk=target_event_reply_queue.id
            ).delete()

        return

    #lambda successful

    #get data
    lambda_response_data = serializer.validated_data
    datetime_now = get_datetime_now()

    #update audio clip

    if target_audio_clip.generic_status.generic_status_name == 'processing':

        AudioClips.objects.filter(
            pk=target_audio_clip.id,
        ).update(
            audio_duration_s=lambda_response_data['audio_duration_s'],
            audio_volume_peaks=lambda_response_data['audio_volume_peaks'],
            audio_file=determined_processed_upload_key,
            generic_status=GenericStatuses.objects.get(generic_status_name='ok'),
            last_modified=datetime_now
        )

    #update event

    if target_event.generic_status.generic_status_name in ['processing', 'incomplete']:

        event_generic_status_name = ''

        if target_audio_clip.audio_clip_role.audio_clip_role_name == 'originator':

            event_generic_status_name = 'incomplete'

        elif target_audio_clip.audio_clip_role.audio_clip_role_name == 'responder':

            event_generic_status_name = 'completed'

        Events.objects.filter(
            pk=target_event.id,
        ).update(
            generic_status=GenericStatuses.objects.get(generic_status_name=event_generic_status_name),
            last_modified=datetime_now
        )

    #delete queue for responder

    if target_audio_clip.audio_clip_role.audio_clip_role_name == 'responder':

        EventReplyQueues.objects.filter(
            pk=target_event_reply_queue.id
        ).delete()

    #delete lambda call record from cache on success

    processing_cache['processings'].pop(str(audio_clip_id))

    CreateAudioClips.set_processing_cache(
        processing_cache_key=processing_cache_key,
        processing_cache=processing_cache
    )

    return















