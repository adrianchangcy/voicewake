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

    try:

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
            fail_silently=False
        )

    except Exception as e:
        raise custom_error(e, __name__, e)


#will validate and invalidate
#must be able to invalidate, since task can potentially start much later than when originally called
@shared_task
def task_normalisation(user_id:int, processing_cache_key:str, audio_clip_id:int, event_id:int):

    #get cache
    processing_cache = cache.get(processing_cache_key, None)

    if processing_cache is None:

        #cache must exist
        raise custom_error(
            ValueError,
            __name__,
            dev_message="No cache found."
        )

    if processing_cache['processings'].get(str(audio_clip_id), None) is None:

        #processing must exist
        raise custom_error(
            ValueError,
            __name__,
            dev_message="No processing found."
        )

    processing_cache_processing = processing_cache['processings'][str(audio_clip_id)]

    if processing_cache_processing['is_processing'] is True:

        #already processing
        raise custom_error(
            ValueError,
            __name__,
            dev_message="Already processing."
        )

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

    #check db if can normalise

    can_normalise = CreateAudioClips.check_db_can_normalise(
        audio_clip=target_audio_clip,
        event=target_event,
        event_reply_queue=target_event_reply_queue
    )

    if can_normalise is False:

        #remove processing

        processing_cache['processings'].pop(processing_cache_key)

        CreateAudioClips.set_processing_cache(
            processing_cache_key=processing_cache_key,
            processing_cache=processing_cache
        )

        raise custom_error(
            ValueError,
            __name__,
            dev_message="Can no longer normalise."
        )

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

    processing_cache['processings'][str(audio_clip_id)]['is_processing'] = True
    processing_cache['processings'][str(audio_clip_id)]['attempts_left'] -= 1

    CreateAudioClips.set_processing_cache(
        processing_cache_key=processing_cache_key,
        processing_cache=processing_cache
    )

    lambda_response_data = None

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

    finally:

        #no longer processing
        processing_cache['processings'][str(audio_clip_id)]['is_processing'] = False

        CreateAudioClips.set_processing_cache(
            processing_cache_key=processing_cache_key,
            processing_cache=processing_cache
        )

    #refetch rows from db to prevent race condition
    #will raise DoesNotExist if they've been deleted

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

    #check db if can normalise

    can_normalise = CreateAudioClips.check_db_can_normalise(
        audio_clip=target_audio_clip,
        event=target_event,
        event_reply_queue=target_event_reply_queue
    )

    if can_normalise is False:

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

    if (
        serializer.is_valid() is False or
        serializer.validated_data['lambda_status_code'] != 200
    ):

        #evaluate attempts again

        if processing_cache['processings'][str(audio_clip_id)]['attempts_left'] > 0:

            return

        #max attempts reached

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
    generic_status_ok = GenericStatuses.objects.get(generic_status_name='ok')
    datetime_now = get_datetime_now()

    #update audio clip

    if target_audio_clip.generic_status.generic_status_name == 'processing':

        AudioClips.objects.filter(
            pk=target_audio_clip.id,
        ).update(
            audio_duration_s=lambda_response_data['audio_duration_s'],
            audio_volume_peaks=lambda_response_data['audio_volume_peaks'],
            audio_file=determined_processed_upload_key,
            generic_status=generic_status_ok,
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

    #ensure cache is up-to-date to avoid race condition
    processing_cache = cache.get(processing_cache_key, None)

    if processing_cache is None:

        raise custom_error(
            ValueError,
            __name__,
            dev_message="Cache is unexpectedly None after normalisation success."
        )

    processing_cache['processings'].pop(str(audio_clip_id))

    CreateAudioClips.set_processing_cache(
        processing_cache_key=processing_cache_key,
        processing_cache=processing_cache
    )

    return















