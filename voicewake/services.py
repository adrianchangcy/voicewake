#here, we define helpers

#Django libraries
from django.db.models import Q, Case, When, Value, F
from django.db import connection
from django.core.files import File
from rest_framework.response import Response
from rest_framework import status
from django_otp.oath import TOTP
from django.contrib.auth import get_user_model
from django.db import transaction
from django.template.loader import get_template
from django.core.mail import send_mail
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.core.files.base import ContentFile
from django.db import connection
from django.core.cache import cache
from django_celery_beat.models import PeriodicTask

#Python
from datetime import datetime, timezone, timedelta, tzinfo
from genericpath import isfile
from zoneinfo import ZoneInfo
import secrets
import time
import re
import math
import subprocess
import json
from typing import Union
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
from typing import Literal
import base64
from urllib.parse import quote, unquote
import random
from django.db import connection
import inspect
import platform
import logging
import requests
import functools
import sys

#AWS
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

#app files
from .models import *
from .serializers import *


#also deletes uer_x folder if empty after deletion
#meant to serve as 'always replace' logic on "record again" action
def delete_audio_file(absolute_path):

    if os.path.exists(absolute_path) and os.path.isfile(absolute_path):

        #delete precisely the file in source path
        os.remove(absolute_path)

        #delete uer_x folder if it now has 0 files
        for root, dirs, files in os.walk(os.path.dirname(absolute_path), topdown=True):

            if len(dirs) == 0 and len(files) == 0:

                shutil.rmtree(root)

        return True

    return False


def get_datetime_now(to_string:bool=False):

    datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))

    if to_string is True:

        return datetime_now.strftime('%Y-%m-%d %H:%M:%S %z')
    
    return datetime_now

    #to get difference
        #minutes_passed = (get_datetime_now() - event_reply_queue.when_locked).total_seconds() / 60
        #hours_passed = (get_datetime_now() - event_reply_queue.when_locked).total_seconds() / 60 / 60


def get_datetime_from_string(datetime_string:str):

    #follows same format as get_datetime_now
    return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S %z')

    #datetime.strptime()
        #for Python >= 3.2, if format has %z, timezone is maintained
        #deducting then doing .total_seconds() also works
        #e.g.:
            #datetime.strptime(get_datetime_now(to_string=True), '%Y-%m-%d %H:%M:%S %z')


def get_pretty_datetime(seconds:int)->str:

    interval = 0

    if seconds < 60 and seconds >= 0:
        return str(interval) + ' seconds'
    elif seconds < 0:
        return ''

    interval = math.floor(seconds / 60)
    if interval == 1:
        return str(interval) + ' minute'
    elif interval < 60:
        return str(interval) + ' minutes'

    interval = math.floor(seconds / 3600)
    if interval == 1:
        return str(interval) + ' hour'
    elif interval < 24:
        return str(interval) + ' hours'

    interval = math.floor(seconds / 86400)
    if interval == 1:
        return str(interval) + ' day'
    elif interval < 28:
        #fastest transition to '1 month ago', for aesthetic reasons only
        return str(interval) + ' days'

    interval = math.floor(seconds / 2592000)
    if interval < 1:
        #need this, since 2592000 is 30 days, and we are doing < 28
        return '1 month'
    elif interval == 1:
        return str(interval) + ' month'
    elif interval < 12:
        return str(interval) + ' months'

    interval = math.floor(seconds / 31536000)
    if interval == 1:
        return str(interval) + ' year'

    return str(interval) + ' years'


def remove_all_whitespace(string_value):

    return re.sub(r'\s+', '', string_value)


def has_numbers_only(string_value):

    return re.match(r'^[0-9]+$', string_value) is not None


def group_audio_clips_into_events(audio_clips:list[AudioClips])->list:

    sorted_audio_clips = []
    event_ids = []  #simpler way to check and get element position in sorted_audio_clips

    for row in audio_clips:

        if row.event.id not in event_ids:

            #this is what frontend expects
            sorted_audio_clips.append({
                'event': row.event,
                'originator': [],
                'responder': [],
            })

            #skip this event for next audio clips
            event_ids.append(row.event.id)

        if row.audio_clip_role.audio_clip_role_name == 'originator':

            sorted_audio_clips[event_ids.index(row.event.id)]['originator'].append(row)

        else:

            sorted_audio_clips[event_ids.index(row.event.id)]['responder'].append(row)

    return sorted_audio_clips


def extract_event_reply_queues_once_per_event(audio_clips:list[AudioClips])->list:

    #pass in fetched AudioClips
    #EventReplyQueues is then attached to AudioClips.Events, leading to AudioClips.Events.EventReplyQueues structure
    #we extract unique EventReplyQueues

    event_ids = []
    event_reply_queues = []

    for row in audio_clips:

        if row.event.id in event_ids:

            continue

        event_reply_queues.append(
            getattr(row.event, 'eventreplyqueues', None)
        )

    return event_reply_queues


def group_audio_clips_into_events_and_event_reply_queues(audio_clips:list[AudioClips], event_reply_queues:list=[])->list:

    #separate this into its own function to have assurance on separated efficiency
    #we sometimes have EventReplyQueues on an each-audio-clip basis, while sometimes on each-event basis
    #we choose each-event basis

    sorted_audio_clips = []
    event_ids = []  #simpler way to check and get element position in sorted_audio_clips

    for row in audio_clips:

        if row.event.id not in event_ids:

            #this is what frontend expects
            sorted_audio_clips.append({
                'event': row.event,
                'originator': [],
                'responder': [],
                'event_reply_queue': event_reply_queues[len(event_ids)],
            })

            #prevent any future audio_clips from relooping same events
            event_ids.append(row.event.id)

        if row.audio_clip_role.audio_clip_role_name == 'originator':

            sorted_audio_clips[event_ids.index(row.event.id)]['originator'].append(row)

        else:

            sorted_audio_clips[event_ids.index(row.event.id)]['responder'].append(row)

    return sorted_audio_clips


def prevent_events_from_queuing_twice_for_reply(user, events:list):

    datetime_now = get_datetime_now()
    bulk_user_events = []
    user_ids = []
    event_ids = []

    for event in events:

        if user.id not in user_ids and event not in event_ids:

            bulk_user_events.append(
                UserEvents(
                    user=user,
                    event=event,
                    when_excluded_for_reply=datetime_now,
                )
            )

            user_ids.append(user.id)
            event_ids.append(event.id)

    UserEvents.objects.bulk_create(
        bulk_user_events,
        ignore_conflicts=True
    )


def get_user_create_events_and_replies_cooldown_s(user, context:Literal['create_event','create_reply'])->int:

    if context not in ['create_event', 'create_reply']:

        raise ValueError('Invalid context.')

    #this is for "X max new posts every __", which in this case is every 24h
    datetime_now = get_datetime_now()
    datetime_checkpoint = datetime_now.strftime('%Y-%m-%d 00:00:00.%f %z')
    datetime_checkpoint_raw = datetime.strptime(datetime_checkpoint, '%Y-%m-%d %H:%M:%S.%f %z')

    audio_clip_role_name = ''
    count_limit = 0

    if context == 'create_event':

        audio_clip_role_name = 'originator'
        count_limit = settings.EVENT_CREATE_DAILY_LIMIT

    elif context == 'create_reply':

        audio_clip_role_name = 'responder'
        count_limit = settings.EVENT_REPLY_DAILY_LIMIT

    the_count = AudioClips.objects.filter(
        user=user,
        when_created__gte=datetime_checkpoint,
        audio_clip_role__audio_clip_role_name=audio_clip_role_name
    ).count()

    if the_count < count_limit:

        return 0

    #get next 00:00:00 day, and get difference from now
    difference_s = ((datetime_checkpoint_raw + timedelta(days=1)) - datetime_now).total_seconds()

    return math.ceil(difference_s)


def get_datetime_between(timeframe:Literal['day', 'week', 'month', 'all']='all'):

    datetime_checkpoint_timedelta = {
        'day': timedelta(days=1),
        'week': timedelta(days=7),
        'month': timedelta(days=31)
    }

    #calculate time range
    #leave datetime_from as '' if you want "of all time"
    datetime_from = ''
    datetime_to = get_datetime_now(True)

    #determine earliest possible datetime
    if timeframe in datetime_checkpoint_timedelta:

        datetime_from = (get_datetime_now() - datetime_checkpoint_timedelta[timeframe]).strftime('%Y-%m-%d %H:%M:%S.%f %z')

    else:

        #getting earliest audio_clips.when_created adds 5-10ms
        #using custom function get_id_of_events_by_when_created() adds 40ms+
        #arbitrary datetime that is guaranteed beyond earliest audio_clips row is the best so far
        datetime_from = '2020-01-01 01:01:01 +00'

    return {
        'datetime_from': datetime_from,
        'datetime_to': datetime_to
    }


def datetime_to_raw_sql_string(datetime_object:datetime)->str:

    #must include milliseconds, i.e. %f
    #without it, = comparison will be false, as PostgreSQL has %f in db
    return datetime_object.strftime('%Y-%m-%d %H:%M:%S.%f %z')


def get_datetime_difference_s(main_datetime, deducting_datetime)->int:

    return math.ceil((main_datetime - deducting_datetime).total_seconds())


def encode_cursor_token(token_data)->str:

    token_data = json.dumps(token_data)
    token_data = bytes(token_data, 'utf8')
    token_data = base64.urlsafe_b64encode(token_data)
    token_data = quote(token_data)

    return token_data


def decode_cursor_token(token_data:str):

    token_data = unquote(token_data)
    token_data = base64.urlsafe_b64decode(token_data)
    token_data = bytes.decode(token_data, 'utf8')
    token_data = json.loads(token_data)

    return token_data


def get_serializer_error_message(serializer)->str:

    for key in serializer.errors:
        for first_error in serializer.errors[key]:
            return key + ": " + first_error

    return ''


def copy_to_clipboard(full_string:str):

    #https://stackoverflow.com/a/17371323

    if platform.system() == 'Darwin':

        #Mac
        subprocess.run("pbcopy", text=True, input=full_string)

    else:

        subprocess.run("clip", text=True, input=full_string)


def print_testable_sql(full_sql, full_params):

    with connection.cursor() as cursor:

        full_sql = cursor.mogrify(full_sql, full_params)

        print(full_sql)
        copy_to_clipboard(full_sql)
        print('Full mogrify() has been copied to clipboard.')


def custom_error(error_class:Exception, __name__context:str, dev_message="", user_message="")->Exception:

    #demo
    # try:
    #     raise custom_error(ValueError, __name__, "yo fix this", "hehe oops")
    # except ValueError as e:
    #     print(get_user_message_from_custom_error(e))
    #     raise custom_error(e, __name__, e)

    #some exceptions contain non-strings instead, so always ensure dev_message is str() so we can log the entire thing
    dev_message = str(dev_message)

    #for now, we only log errors that are meant for developers
    if dev_message != "":

        logger = None

        #determine whether to use local file or AWS CloudWatch

        #pass __name__ into __name__context, which returns strings such as voicewake.views.... from which __name__ was called
        #can specify __name__ that does not yet exist, which will be auto-created
        logger = logging.getLogger(__name__context)

        #log, with attention to logger's severity level
        #only log at equal or higher severity
        logger.exception(__name__context + " : " + dev_message)

    #pass {} into Exception as *args, which can later be retrieved with Exception.args[0]
    return error_class({
        "dev_message": dev_message,
        "user_message": user_message
    })

def get_user_message_from_custom_error(new_error:Exception)->str:

    try:
        return new_error.args[0]['user_message']
    except:
        return ""

def get_dev_message_from_custom_error(new_error:Exception)->str:

    try:
        return new_error.args[0]['dev_message']
    except:
        return ""


def print_with_function_name(extra_stuff_to_print)->str:

    #this gives you outer function's name, i.e. not print_with_function_name()
    cframe = inspect.currentframe()
    calling_function_name = inspect.getframeinfo(cframe.f_back).function + "()"
    print("\n" + calling_function_name + ": " + str(extra_stuff_to_print) + "\n")


def get_response_data(request):

    response_data = (bytes(request.content).decode())
    return json.loads(response_data)


def do_celery_beat_healthcheck():

    #call this at healthcheck via:
    #python manage.py shell -c "from voicewake.services import do_celery_beat_healthcheck; do_celery_beat_healthcheck();"

    #check cache key
    target_cache = cache.get(settings.CELERY_BEAT_HEALTHCHECK_CACHE_KEY, None)

    if target_cache is None:

        #container is unhealthy
        print('CeleryBeat healthcheck: exit 1.')
        sys.exit(1)

    #container is healthy
    print('CeleryBeat healthcheck: exit 0.')
    sys.exit(0)


def delete_celery_task_from_db(task_name=''):

    #call this everytime you make a change in relation to Celery Beat
    #otherwise periodic tasks from Celery Beat will permanently show up
    #celery purge does not work, since purge only deletes message, not task
    #in our scenario, it persists via CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

    try:

        if task_name == '':

            PeriodicTask.objects.all().delete()

        else:

            PeriodicTask.objects.filter(name=task_name).delete()

        print('CeleryBeat deleting periodic tasks: exit 0.')
        sys.exit(0)

    except Exception as e:

        print(e)
        print('CeleryBeat deleting periodic tasks: exit 1.')
        sys.exit(1)



class Stopwatch:

    def __init__(self):

        self.start_time = None
        self.stop_time = None


    def start(self):

        self.start_time = time.perf_counter()
        self.stop_time = None


    def stop(self):

        self.stop_time = time.perf_counter()


    def diff_seconds(self):

        #0.000s
        return round(self.stop_time - self.start_time, 3)



#for OTP
class TOTPVerification:

    #thanks to link below
    #https://medium.com/viithiisys/creating-and-verifying-one-time-passwords-with-django-otp-861f472f602f

    def __init__(self, totp_number_of_digits, totp_validity_seconds, totp_tolerance_seconds):

        #1 byte is 8 bits, so therefore minimum 15 bytes, recommended 20 bytes
        #it seems that key must always be a new random one on every new token
        #else you will forever get the same token, all things being equal
        self.key = None

        # counter with which last token was verified.
        # Next token must be generated at a higher counter value.
        self.last_verified_counter = -1

        # this value will return True, if a token has been successfully
        # verified.
        self.verified = False

        # number of digits in a token. Default is 6.
        self.totp_number_of_digits = totp_number_of_digits

        # validity period of a token. Default is 30 seconds.
        self.token_validity_period = totp_validity_seconds

        self.token_validity_tolerance = totp_tolerance_seconds


    def totp_obj(self):

        # create a TOTP object
        totp = TOTP(
            key=self.key,
            step=self.token_validity_period,
            digits=self.totp_number_of_digits
        )

        # the current time will be used to generate a counter
        totp.time = time.time()

        return totp


    def set_key(self, key):

        self.key = key


    def create_key(self, totp_key_byte_size):

        self.key = secrets.token_bytes(totp_key_byte_size)


    def get_key(self):

        return self.key


    def generate_token(self):

        # get the TOTP object and use that to create token
        totp = self.totp_obj()

        # token can be obtained with `totp.token()`
        token = str(totp.token())
        token = token.zfill(self.totp_number_of_digits)
        return token


    def verify_token(self, token):

        try:

            # convert the input token to integer
            token = int(token)

        except ValueError:

            # return False, if token could not be converted to an integer
            self.verified = False
            print('Could not convert token to int.')

        else:

            totp = self.totp_obj()

            # check if the current counter value is higher than the value of
            # last verified counter and check if entered token is correct by
            # calling totp.verify_token()
            if (totp.t() > self.last_verified_counter) and totp.verify(token, tolerance=self.token_validity_tolerance) is True:

                # if the condition is true, set the last verified counter value
                # to current counter value, and return True
                self.last_verified_counter = totp.t()
                self.verified = True

            else:

                # if the token entered was invalid or if the counter value
                # was less than last verified counter, then return False
                self.verified = False

        return self.verified



#inherits TOTPVerification class
#always use this class in transaction.atomic()
#vulnerable to malicious locking, would require a few extra steps to mitigate, but rare to see in practice
#would prefer using Google/others before implementing django-otp
class HandleUserOTP(TOTPVerification):

    def __init__(
        self, user_instance,
        totp_number_of_digits, totp_validity_seconds, totp_tolerance_seconds,
        otp_creation_timeout_seconds, otp_max_creations, otp_max_creations_timeout_seconds,
        otp_max_attempts, otp_max_attempts_timeout_seconds
    ):

        self.user_instance = user_instance
        self.user_otp_instance = None
        self.otp = ''

        self.otp_creation_timeout_seconds = otp_creation_timeout_seconds
        self.otp_max_creations = otp_max_creations
        self.otp_max_creations_timeout_seconds = otp_max_creations_timeout_seconds

        self.otp_max_attempts = otp_max_attempts
        self.otp_max_attempts_timeout_seconds = otp_max_attempts_timeout_seconds

        TOTPVerification.__init__(self, totp_number_of_digits, totp_validity_seconds, totp_tolerance_seconds)


    def _set_key_if_none(self):

        if self.key is None:

            self.key = bytes(self.user_instance.totp_key)


    def guarantee_user_otp_instance(self, select_for_update=False):

        if self.user_otp_instance is not None:

            return

        if select_for_update is True:

            self.user_otp_instance, created = UserOTP.objects.select_for_update().get_or_create(
                user=self.user_instance
            )

        else:

            self.user_otp_instance, created = UserOTP.objects.get_or_create(
                user=self.user_instance
            )

        return 


    def get_user_instance(self):

        return self.user_instance


    def get_user_otp_instance(self):

        return self.user_otp_instance


    def get_otp_attempt_timeout_seconds_left(self):

        time_remaining = 0

        if self.user_otp_instance.otp_attempts == 0 and self.user_otp_instance.otp_last_attempted is None:

            #haven't started attempting OTP
            return time_remaining

        datetime_now = get_datetime_now()
        timeout_end = self.user_otp_instance.otp_last_attempted + timedelta(seconds=self.otp_max_attempts_timeout_seconds)

        if datetime_now >= timeout_end:

            #timeout is over, disregard attempts, reset
            #we disregard attempts to prevent "tried 3/4 times last week, 1 time today triggers timeout"

            self.user_otp_instance.otp_attempts = 0
            self.user_otp_instance.otp_last_attempted = None
            self.user_otp_instance.save()

            time_remaining = 0
            return time_remaining

        else:

            #timeout is not over

            if self.user_otp_instance.otp_attempts < self.otp_max_attempts:

                #as long as below max attempts, no timeout
                time_remaining = 0
                return time_remaining
            
            else:

                #has max attempts
                time_remaining = (timeout_end - datetime_now).total_seconds()
                return math.ceil(time_remaining)


    def get_otp_creation_timeout_seconds_left(self):

        time_remaining = 0

        if self.user_otp_instance.otp_creations == 0 and self.user_otp_instance.otp_last_created is None:

            #haven't started creating OTP
            return time_remaining
        
        datetime_now = get_datetime_now()
        otp_max_creations_timeout_end = self.user_otp_instance.otp_last_created + timedelta(seconds=self.otp_max_creations_timeout_seconds)
        otp_last_created_timeout_end = self.user_otp_instance.otp_last_created + timedelta(seconds=self.otp_creation_timeout_seconds)

        if datetime_now >= otp_max_creations_timeout_end:

            #disregard creation count, always reset, as count is now irrelevant
            #we disregard count to prevent "created 3/4 times last week, 1 time today triggers timeout"

            self.user_otp_instance.otp_creations = 0
            self.user_otp_instance.otp_last_created = None
            self.user_otp_instance.save()

            time_remaining = 0
            return time_remaining
        
        #not yet at max timeout, continue

        if self.user_otp_instance.otp_creations < self.otp_max_creations:

            #not yet at max creations, evaluate with smaller timeout

            if datetime_now >= otp_last_created_timeout_end:

                #is past smaller timeout
                time_remaining = 0
                return time_remaining
            
            else:

                #still under smaller timeout
                time_remaining = (otp_last_created_timeout_end - datetime_now).total_seconds()
                return math.ceil(time_remaining)

        else:

            #has max creations, evaluate with max timeout

            time_remaining = (otp_max_creations_timeout_end - datetime_now).total_seconds()
            return math.ceil(time_remaining)


    def generate_otp(self)->str:

        self._set_key_if_none()

        if self.get_otp_creation_timeout_seconds_left() > 0:

            return ''

        self.user_otp_instance.otp_creations += 1
        self.user_otp_instance.otp_last_created = get_datetime_now()
        self.user_otp_instance.save()

        self.otp = self.generate_token()

        return self.otp


    def verify_otp(self, otp:str):

        self._set_key_if_none()

        #creation and attempt are managed separately
        #so evaluating attempt only is proper
        if self.user_otp_instance is None or self.get_otp_attempt_timeout_seconds_left() > 0:

            return False

        #check token validity
        if self.verify_token(otp) is False:

            self.user_otp_instance.otp_attempts += 1
            self.user_otp_instance.otp_last_attempted = get_datetime_now()
            self.user_otp_instance.save()
            return False

        #ok
        self.user_otp_instance.delete()
        self.user_otp_instance = None
        return True



class S3PostWrapper:

    def __init__(
        self,
        is_ec2:bool,
        allowed_unprocessed_file_extensions:list,
        region_name:str,
        s3_audio_file_max_size_b:int,
        unprocessed_bucket_name:str,
        url_expiry_s:int=1000,
        key_exist_retries:int=4,
        post_max_attempts:int=10,
        aws_access_key_id:str='',
        aws_secret_access_key:str='',
    ):

        #process flow
            #frontend POSTs with CSRF token --> backend --> generate pre-signed S3 URL --> ...
            #... --> frontend POSTs to pre-signed S3 URL --> S3 returns 204/422 when done --> ...
            #... --> frontend POSTs to backend --> ...
            #... --> backend receives file info --> POSTs to Lambda via RequestResponse --> ...
            #... --> if Lambda ok, return 200, else delete file in S3 if found

        #policies, if possible
            #1 bucket to dump all unprocessed user files
                #auto-delete if file remains past x days
                #allow only PUT
                #allow only 1 file upload per pre-signed S3 URL
            #1 bucket for processed files
                #proper folder pathing
                #fully private

        #we use POST via generate_presigned_post(), instead of generate_presigned_url()
        #we can have better control over policies and criterias this way

        #passed values
        #os.environ[] always returns string, so we convert
        self.is_ec2 = is_ec2
        self.allowed_unprocessed_file_extensions = allowed_unprocessed_file_extensions
        self.unprocessed_bucket_name = unprocessed_bucket_name
        self.s3_audio_file_max_size_b = int(s3_audio_file_max_size_b)
        self.url_expiry_s = int(url_expiry_s)
        self.key_exist_retries = key_exist_retries

        #S3

        self.s3_client = None

        advanced_config = Config(
            retries={
                'max_attempts': post_max_attempts,
                'mode': 'standard'
            }
        )

        try:

            if is_ec2 is True:

                self.s3_client = boto3.client(
                    service_name='s3',
                    region_name=region_name,
                    config=advanced_config,
                )

            else:

                self.s3_client = boto3.client(
                    service_name='s3',
                    region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    config=advanced_config,
                )

        except ClientError:

            raise custom_error(
                ValueError,
                __name__,
                dev_message='Could not create S3 boto client.',
                user_message='Upload is temporarily unavailable.'
            )


    def check_bucket_exists(self, bucket:str)->bool:

        try:

            #requires "s3:ListBucket" policy
            response = self.s3_client.head_bucket(
                Bucket=bucket,
            )

            if response['ResponseMetadata']['HTTPStatusCode'] != 200:

                raise ValueError('Expected 200 but received ' + str(response['ResponseMetadata']['HTTPStatusCode']))

            return True
        
        except ClientError as e:

            if e.response['ResponseMetadata']['HTTPStatusCode'] == 404:

                return False

            raise e


    def check_object_exists(self, key:str)->bool:

        try:

            #requires "s3:GetObject" and "s3:ListBucket" policy
            response = self.s3_client.head_object(
                Bucket=self.unprocessed_bucket_name,
                Key=key,
            )

            if response['ResponseMetadata']['HTTPStatusCode'] != 200:

                raise ValueError('Expected 200 but received ' + str(response['ResponseMetadata']['HTTPStatusCode']))

            return True

        except ClientError as e:

            if e.response['ResponseMetadata']['HTTPStatusCode'] == 404:

                return False

            raise e


    def generate_unprocessed_object_key(self, user_id:int, file_extension:str):

        if file_extension not in self.allowed_unprocessed_file_extensions:

            raise ValueError(
                file_extension + ' is invalid, must be one of: ' + str(self.allowed_unprocessed_file_extensions)
            )

        datetime_now = get_datetime_now()

        #determine early/first "folder"
        #important in the context of accurate settings + CloudFront origin to handle "/media/"
        #tests should ideally be done entirely in separate buckets, but can't afford 2 CloudFronts for now

        #no starting slash
        #.format() converts args into str for us
        #we want to set MEDIAFILES_LOCATION here, instead of determining via dev/prod at serializer
        #this helps to guarantee the separation between files created in dev and prod
        file_path = '{0}/audio_clips/year_{1}/month_{2}/day_{3}/user_id_{4}/'.format(
            settings.MEDIAFILES_LOCATION,
            datetime_now.strftime('%Y'),
            datetime_now.strftime('%m'),
            datetime_now.strftime('%d'),
            user_id,
        )

        #retry if full key exists

        for retry in range(0, self.key_exist_retries):

            #use secrets.token_hex() instead of AudioClips.id
            #ensures that all AudioClips have .audio_file
            file_key = file_path + secrets.token_hex(16) + '.' + file_extension

            if self.check_object_exists(file_key) is False:

                return file_key

        raise ValueError('Maximum retries reached on check_object_exists().')


    def generate_unprocessed_presigned_post_url(self, key:str, file_extension:str=''):

        #HTTP 422 on condition failure, will not upload
        #HTTP 204 on success
        #for file MimeType, e.g. allow only .mp3, must be done at bucket policy, not here
        #key will be available via upload_info['fields']['key']

        #if file_extension is not passed, determine from passed key
        #this happens when regenerating POST URL

        if len(file_extension) == 0:

            for unprocessed_file_extension in self.allowed_unprocessed_file_extensions:

                current_key_extension = key[
                    -len(unprocessed_file_extension):len(key)
                ]

                if current_key_extension == unprocessed_file_extension:

                    file_extension = unprocessed_file_extension
                    break

            #no match
            if len(file_extension) == 0:

                raise ValueError(
                    key + ' is not of ' + str(self.allowed_unprocessed_file_extensions)
                )

        elif file_extension not in self.allowed_unprocessed_file_extensions:

            raise ValueError(
                file_extension + ' is invalid, must be one of: ' + str(self.allowed_unprocessed_file_extensions)
            )

        conditions = [
            {'bucket': self.unprocessed_bucket_name},
            {'key': key},
            ["starts-with", "$Content-Type", f"audio/{file_extension}"],
            ["content-length-range", 1024, self.s3_audio_file_max_size_b],
        ]

        try:

            return self.s3_client.generate_presigned_post(
                Bucket=self.unprocessed_bucket_name,
                Key=key,
                Fields={"Content-Type": f"audio/{file_extension}"},
                Conditions=conditions,
                ExpiresIn=self.url_expiry_s
            )

        except ClientError as e:

            raise custom_error(
                ValueError,
                __name__,
                dev_message=f"Couldn't generate POST URL for key ({key}): {str(e)}",
                user_message='Upload is temporarily unavailable.'
            )


    @staticmethod
    def s3_post_upload(url, fields, local_file_path):

        with open(local_file_path, mode='rb') as object_file:

            object_file.seek(0)

            #must be 'file'
            #must be last field
            fields['file'] = object_file.read()

        #at Python, form fields are passed as files={}
        response = requests.post(
            url,
            files=fields
        )

        #always returns 204, regardless of whether file already exists in S3 or not
        #tested as of March 2024
        if response.status_code == 204:

            return

        print(response)
        raise ValueError(str(response.status_code) + ' is not 204')


    def delete_object(self, key:str):

        #requires "s3:DeleteObject" policy
        return self.s3_client.delete_object(
            Bucket=self.unprocessed_bucket_name,
            Key=key,
        )



class AWSLambdaWrapper:

    def __init__(
        self,
        is_ec2:bool,
        timeout_s:int=30,
        max_attempts:int=0,
        region_name:str='',
        aws_access_key_id:str='',
        aws_secret_access_key:str='',
    ):

        self.is_ec2 = is_ec2
        self.region_name = region_name

        #your_lambda --> Configuration --> General configuration --> Edit
        #the timeout value there has higher priority than here
        advanced_config = Config(
            retries={
                'max_attempts': max_attempts,
                'mode': 'standard'
            },
            read_timeout=timeout_s,
            connect_timeout=timeout_s,
        )

        try:

            if is_ec2 is True:

                self.client = boto3.client(
                    service_name='lambda',
                    region_name=region_name,
                    config=advanced_config,
                )

            else:

                self.client = boto3.client(
                    service_name='lambda',
                    region_name=region_name,
                    config=advanced_config,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                )

        except ClientError:

            raise


    def _invoke_lambda(self, function_name:str, payload:dict):

        #at Lambda, retrieve payload in lambda_handler via event.get('keyname')
        #be sure to standardise all Lambdas to return these at minimum:
            #{'lambda_status_code': int, 'lambda_message':str}

        payload = json.dumps(payload)
        payload = bytes(payload, encoding='utf-8')

        response = self.client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=payload
        )

        #get response

        #['Payload'] is StreamingBody object, so we use .read() to get bytes
        #StreamingBody object has no .seek(0), so .read() can only be used once
        #AWS Lambda serializes entire response to JSON
        response_data = response['Payload'].read()
        response_data = bytes(response_data).decode(encoding='utf-8')
        response_data = json.loads(response_data)

        return response_data


    #all params are for payload, and must match AWSLambdaNormaliseAudioClips.__init__()
    def invoke_normalise_audio_clips_lambda(
        self,
        s3_region_name:str='',
        unprocessed_object_key:str='',
        processed_object_key:str='',
        unprocessed_bucket_name:str='',
        processed_bucket_name:str='',
        is_ping:bool=False,
    ):

        #if you just want to check if lambda is ok, pass is_ping=True

        payload = {
            's3_region_name': s3_region_name,
            'unprocessed_object_key': unprocessed_object_key,
            'processed_object_key': processed_object_key,
            'unprocessed_bucket_name': unprocessed_bucket_name,
            'processed_bucket_name': processed_bucket_name,
            'is_ping': is_ping,
            'use_timer': settings.DEBUG,
        }

        return self._invoke_lambda(
            function_name=os.environ['AWS_LAMBDA_NORMALISE_FUNCTION_NAME'],
            payload=payload
        )



class CreateAudioClips():

    #steps:
        #upload: create db records, return s3 endpoint
        #regenerate: get new s3 endpoint
        #process: call Lambda, update records
    #behaviours
        #event.generic_status
            #for both originator/responder, becomes processing when uploaded and ready to normalise

    def __init__(
        self,
        user,
        is_ec2:bool,
        current_context:Literal["create_event", "create_reply"],
        unprocessed_file_extensions:list,
        processed_file_extension:str,
        event_create_daily_limit:int,
        event_reply_daily_limit:int,
        event_reply_expiry_seconds:int,
    ):

        if current_context not in ["create_event", "create_reply"]:

            raise ValueError('Invalid context.')

        if user.is_authenticated is False:

            raise ValueError('User must be logged in.')

        self.user = user
        self.is_ec2 = is_ec2
        self.current_context:Literal["create_event", "create_reply"] = current_context
        self.unprocessed_file_extensions = unprocessed_file_extensions
        self.processed_file_extension = processed_file_extension
        self.event_create_daily_limit = event_create_daily_limit
        self.event_reply_daily_limit = event_reply_daily_limit
        self.event_reply_expiry_seconds = event_reply_expiry_seconds

        self.datetime_now = get_datetime_now()

        self.event = None
        self.event_reply_queue = None
        self.audio_clip = None

        self.s3_post_wrapper = None

        self.processing_cache_key = ''
        self.processing_cache = None


    #not a static method because it is easier to use when class is initiated
    def get_cooldown_on_audio_clip_create_limit_s(self)->int:

        #this is for "X max new posts every __", which in this case is every 24h

        passed_midnight_today_string = self.datetime_now.strftime('%Y-%m-%d 00:00:00.%f %z')
        passed_midnight_today = datetime.strptime(
            passed_midnight_today_string,
            '%Y-%m-%d %H:%M:%S.%f %z'
        )

        audio_clip_role_name = ''
        count_limit = 0

        if self.current_context == 'create_event':

            audio_clip_role_name = 'originator'
            count_limit = self.event_create_daily_limit

        elif self.current_context == 'create_reply':

            audio_clip_role_name = 'responder'
            count_limit = self.event_reply_daily_limit

        the_count = AudioClips.objects.filter(
            user=self.user,
            when_created__gte=passed_midnight_today_string,
            audio_clip_role__audio_clip_role_name=audio_clip_role_name
        ).count()

        if the_count < count_limit:

            return 0

        #get next 00:00:00 day, and get difference from now
        pretty_difference_s = ((passed_midnight_today + timedelta(days=1)) - self.datetime_now).total_seconds()

        return math.ceil(pretty_difference_s)


    @staticmethod
    def determine_processed_upload_key(
        unprocessed_upload_key:str,
        unprocessed_file_extensions:list,
        processed_file_extension:str,
    )->str:

        #we simply swap the extension of unprocessed_upload_key
        #we don't have to do detailed string checks
            #will compare directly with AudioClips.audio_file for validation

        if (
            len(unprocessed_upload_key) == 0 or
            len(unprocessed_file_extensions) == 0 or
            len(processed_file_extension) == 0
        ):

            raise custom_error(
                ValueError,
                __name__,
                dev_message='Invalid.',
            )

        #file extension is not yet of processed type
        #we determine what the processed key looks like, by simply swapping the extension properly

        #when counting position from end, it starts from index -1, not 0
            #index 2 lands you on 0,1,2nd, but -2 lands you on -1,-2

        for unprocessed_file_extension in unprocessed_file_extensions:

            current_upload_key_extension = unprocessed_upload_key[
                -len(unprocessed_file_extension):len(unprocessed_upload_key)
            ]

            if current_upload_key_extension == unprocessed_file_extension:

                processed_upload_key = unprocessed_upload_key[0:-len(unprocessed_file_extension)]

                processed_upload_key += processed_file_extension

                #return appropriate processed key
                return processed_upload_key

            elif current_upload_key_extension == processed_file_extension:

                #already with processed file extension
                #return '' for better error handling
                return ''

        raise custom_error(
            ValueError,
            __name__,
            dev_message=f'''
                upload_key {unprocessed_upload_key} is not of 
                {str(unprocessed_file_extensions)}
            '''
        )


    @staticmethod
    def determine_processing_cache_key(user_id:int)->str:

        return (
            'audio_clip_processing_store_' + str(user_id)
        )


    #main cache, every user has one
    @staticmethod
    def get_default_processing_cache_main_object()->dict:

        #use audio_clip.id as key for processings
        #frontend can call this to sync its store at 1-to-1 at any time
        #frontend can refer to last_updated to check whether it is out of sync
        return {
            'processings': {},
            'last_updated': get_datetime_now(),
        }


    #get default processing, with audio_clip and event data filled in
    @staticmethod
    def get_default_processing_cache_processing_object(event:Events, audio_clip:AudioClips)->dict:

        if event is None:

            raise custom_error(
                ValueError,
                __name__,
                dev_message="Missing event when it is needed to add to processing."
            )

        if audio_clip is None:

            raise custom_error(
                ValueError,
                __name__,
                dev_message="Missing audio_clip when it is needed to add to processing."
            )

        return {
            'audio_clip_role_name': audio_clip.audio_clip_role.audio_clip_role_name,
            'event': {
                'id': event.id,
                'event_name': event.event_name,
            },
            'audio_clip_tone': {
                'id': audio_clip.audio_clip_tone.id,
                'audio_clip_tone_name': audio_clip.audio_clip_tone.audio_clip_tone_name,
                'audio_clip_tone_symbol': audio_clip.audio_clip_tone.audio_clip_tone_symbol,
            },
            'is_processing': False,
            'attempts_left': settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS,
        }


    #extract processing from cache
    @staticmethod
    def get_processing_cache_processing_object(processing_cache:dict, audio_clip_id:int)->dict|None:

        return processing_cache['processings'].get(str(audio_clip_id), None)


    #validate db side of things
    @staticmethod
    def check_db_can_normalise(audio_clip, event, event_reply_queue)->bool:

        #if cannot normalise, only reset those that match normalise conditions
        #this is to maintain and respect any higher precedence statuses

        audio_clip_role_name = audio_clip.audio_clip_role.audio_clip_role_name

        if audio_clip_role_name == 'originator':

            if audio_clip is None or event is None:

                raise custom_error(
                    ValueError,
                    __name__,
                    dev_message="Missing args."
                )

            can_normalise = (
                audio_clip.generic_status.generic_status_name == 'processing' and
                event.generic_status.generic_status_name == 'processing'
            )

            if can_normalise is False:

                if audio_clip.generic_status.generic_status_name == 'processing':

                    audio_clip.generic_status = GenericStatuses.objects.get(generic_status_name='deleted')
                    audio_clip.save()

                if event.generic_status.generic_status_name == 'processing':

                    #we don't need event to enforce limit
                    event.delete()

            return can_normalise

        elif audio_clip_role_name == 'responder':

            if audio_clip is None or event is None or event_reply_queue is None:

                raise custom_error(
                    ValueError,
                    __name__,
                    dev_message="Missing args."
                )

            can_normalise = (
                audio_clip.generic_status.generic_status_name == 'processing' and
                event.generic_status.generic_status_name == 'incomplete' and
                event_reply_queue.is_replying is True and
                get_datetime_now() < (event_reply_queue.when_locked + timedelta(seconds=settings.EVENT_REPLY_MAX_DURATION_S))
            )

            if can_normalise is False:

                if audio_clip.generic_status.generic_status_name == 'processing':

                    audio_clip.generic_status = GenericStatuses.objects.get(generic_status_name='deleted')
                    audio_clip.save()

                event_reply_queue.delete()

            return can_normalise

        raise custom_error(
            ValueError,
            __name__,
            dev_message="Not originator/responder."
        )


    #use this when setting cache, so we can consistently update last_updated
    #last_updated is important to check whether frontend store is in sync
    @staticmethod
    def set_processing_cache(processing_cache_key:str, processing_cache:dict):

        processing_cache['last_updated'] = get_datetime_now()

        cache.set(
            processing_cache_key,
            processing_cache,
            timeout=None,
        )


    def _ensure_processing_cache_exists(self):

        if (
            self.processing_cache_key != '' and
            self.processing_cache is not None and
            self.processing_cache['processings'].get(str(self.audio_clip.id), None) is not None
        ):

            return

        self.processing_cache_key = self.determine_processing_cache_key(user_id=self.user.id)

        #if cache does not exist, create default cache, save, and use it
        #if cache exists, use the cache

        target_cache = cache.get(self.processing_cache_key, None)
        must_set_cache = False

        if target_cache is None:

            self.processing_cache = self.get_default_processing_cache_main_object()

            must_set_cache = True

        else:

            self.processing_cache = target_cache

        #add processing if it does not exist

        if self.processing_cache['processings'].get(str(self.audio_clip.id), None) is None:

            self.processing_cache['processings'].update({
                str(self.audio_clip.id): self.get_default_processing_cache_processing_object(
                    event=self.event,
                    audio_clip=self.audio_clip,
                ),
            })

            self.processing_cache['last_updated'] = get_datetime_now()

            must_set_cache = True

        #set cache if needed

        if must_set_cache is True:

            #cache must already exist, as task queue will not create on its own
            #since cache rows are user-specific, timeout is not needed
            self.set_processing_cache(processing_cache_key=self.processing_cache_key, processing_cache=self.processing_cache)


    def _initialise_s3_post_wrapper(self):

        self.s3_post_wrapper = S3PostWrapper(
            is_ec2=self.is_ec2,
            allowed_unprocessed_file_extensions=self.unprocessed_file_extensions,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=int(os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B']),
            url_expiry_s=int(os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S']),
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )


    def _initialise_lambda_wrapper(self):

        self.lambda_wrapper = AWSLambdaWrapper(
            is_ec2=self.is_ec2,
            timeout_s=int(os.environ['AWS_LAMBDA_NORMALISE_TIMEOUT_S']),
            region_name=os.environ['AWS_LAMBDA_REGION_NAME'],
            aws_access_key_id=os.environ['AWS_LAMBDA_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_LAMBDA_SECRET_ACCESS_KEY'],
        )


    #creates event + audio_clip, returns audio_clip.id
    #returns 201, every call will create new records
    def create_records_and_return_s3_endpoint_as_originator(
        self,
        event_name:str,
        audio_clip_tone_id:int,
        recorded_file_extension:str,
    )->Response:

        if self.current_context != "create_event":

            raise custom_error(
                ValueError,
                __name__,
                dev_message="Invalid self.current_context."
            )

        #check if creation limit has been reached

        cooldown_s = self.get_cooldown_on_audio_clip_create_limit_s()

        if cooldown_s > 0:

            return Response(
                data={
                    "message": "Come back in " + get_pretty_datetime(cooldown_s) + "!",
                    "event_create_daily_limit_reached": True,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #proceed

        audio_clip_role = AudioClipRoles.objects.get(audio_clip_role_name='originator')
        audio_clip_tone = AudioClipTones.objects.get(pk=audio_clip_tone_id)
        generic_status_processing = GenericStatuses.objects.get(generic_status_name='processing')

        #create event, as "processing", to avoid being queued for responders
        self.event = Events.objects.create(
            event_name=event_name,
            generic_status=generic_status_processing,
            created_by=self.user,
        )

        #s3

        self._initialise_s3_post_wrapper()

        #generate key and presigned URL

        upload_key = self.s3_post_wrapper.generate_unprocessed_object_key(
            user_id=self.user.id,
            file_extension=recorded_file_extension
        )

        upload_info = self.s3_post_wrapper.generate_unprocessed_presigned_post_url(
            key=upload_key,
            file_extension=recorded_file_extension,
        )

        #create AudioClips

        #we update audio_volume_peaks and audio_duration_s during processing, not here
        #audio_file currently has file extension of unprocessed file
        self.audio_clip = AudioClips.objects.create(
            user=self.user,
            audio_clip_role=audio_clip_role,
            audio_clip_tone=audio_clip_tone,
            event=self.event,
            audio_volume_peaks=[],
            audio_duration_s=0,
            audio_file=upload_key,
            generic_status=generic_status_processing
        )

        return Response(
            data={
                'upload_url': upload_info['url'],
                'upload_fields': json.dumps(upload_info['fields']),
                'event_id': self.event.id,
                'audio_clip_id': self.audio_clip.id,
            },
            status=status.HTTP_201_CREATED
        )


    #creates event + audio_clip, returns audio_clip.id
    #returns 201, first call will create new records, or return existing records
    #will validate + invalidate
    def create_records_and_return_s3_endpoint_as_responder(
        self,
        event_id:int,
        audio_clip_tone_id:int,
        recorded_file_extension:str,
    )->Response:

        #reply limit is enforced at choice listing, not here

        if self.current_context != "create_reply":

            raise custom_error(
                ValueError,
                __name__,
                dev_message="Invalid self.current_context."
            )

        #handle audio clip first so we can immediately return if processed

        try:

            self.audio_clip = AudioClips.objects.select_related(
                'generic_status',
            ).get(
                event_id=event_id,
                user_id=self.user.id,
                audio_clip_role__audio_clip_role_name='responder',
            )

            #check if already processed
            #queue no longer exists when true
            #also more manageable than having frontend call "check status" API every time
            if self.audio_clip.generic_status.generic_status_name == 'ok':

                return Response(
                    data={
                        'is_processed': True,
                    },
                    status=status.HTTP_200_OK
                )

            elif self.audio_clip.generic_status.generic_status_name != 'processing':

                #audio clip exists, but is not processing
                #do nothing
                return Response(
                    data={
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        except AudioClips.DoesNotExist:

            pass

        except:

            raise

        #check other relevant records

        try:

            #get and check queue

            self.event_reply_queue = EventReplyQueues.objects.select_related(
                'event',
                'event__generic_status'
            ).get(
                event_id=event_id,
                locked_for_user=self.user,
            )

            #get event
            self.event = self.event_reply_queue.event

        except EventReplyQueues.DoesNotExist:

            #no need to do anything
            #audio clip wouldn't exist without queue
            return Response(
                data={
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except:

            raise

        #check if not yet is_replying=True
        if self.event_reply_queue.is_replying is not True:

            return Response(
                data={
                    "message": "Confirm your reply choice first.",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #check whether reply queue has expired

        if(
            self.datetime_now >=
            (self.event_reply_queue.when_locked + timedelta(seconds=self.event_reply_expiry_seconds))
        ):

            #invalidate/reset everything

            if self.audio_clip is not None and self.audio_clip.generic_status.generic_status_name == 'processing':

                self.audio_clip.generic_status = GenericStatuses.objects.get(generic_status_name='deleted')
                self.audio_clip.save()

            self.event_reply_queue.delete()

            return Response(
                data={
                    "message": "Reply choice has just expired.",
                },
                status=status.HTTP_205_RESET_CONTENT
            )

        #check event

        if self.event.generic_status.generic_status_name != 'incomplete':

            #invalidate/reset everything

            if self.audio_clip is not None and self.audio_clip.generic_status.generic_status_name == 'processing':

                self.audio_clip.generic_status = GenericStatuses.objects.get(generic_status_name='deleted')
                self.audio_clip.save()

            self.event_reply_queue.delete()

            return Response(
                data={
                    "message": "Event is no longer available for reply.",
                },
                status=status.HTTP_404_NOT_FOUND
            )

        #proceed

        #s3
        self._initialise_s3_post_wrapper()

        #generate key and presigned URL

        upload_key = self.s3_post_wrapper.generate_unprocessed_object_key(
            user_id=self.user.id,
            file_extension=recorded_file_extension
        )

        upload_info = self.s3_post_wrapper.generate_unprocessed_presigned_post_url(
            key=upload_key,
            file_extension=recorded_file_extension,
        )

        #create audio clip if it does not exist
        if self.audio_clip is None:

            generic_status_processing = GenericStatuses.objects.get(generic_status_name='processing')
            audio_clip_role = AudioClipRoles.objects.get(audio_clip_role_name='responder')
            audio_clip_tone = AudioClipTones.objects.get(pk=audio_clip_tone_id)

            self.audio_clip = AudioClips.objects.create(
                user=self.user,
                audio_clip_role=audio_clip_role,
                audio_clip_tone=audio_clip_tone,
                event_id=event_id,
                audio_volume_peaks=[],
                audio_duration_s=0,
                audio_file=upload_key,
                generic_status=generic_status_processing
            )

        #no need to update event to "processing" as responder
        #otherwise the event cannot be viewed

        return Response(
            data={
                'upload_url': upload_info['url'],
                'upload_fields': json.dumps(upload_info['fields']),
                'event_id': event_id,
                'audio_clip_id': self.audio_clip.id,
            },
            status=status.HTTP_201_CREATED
        )


    #will minimally validate, no invalidation
    def regenerate_s3_endpoint(self, audio_clip_id:int)->Response:

        #check if audio_clip exists
        #users can only get their own records

        audio_clip = None

        try:

            audio_clip = AudioClips.objects.get(
                pk=audio_clip_id,
                user_id=self.user.id,
                generic_status__generic_status_name='processing',
            )

        except AudioClips.DoesNotExist:

            return Response(
                data={
                },
                status=status.HTTP_404_NOT_FOUND
            )

        #use audio_file as key and regenerate presigned URL

        self._initialise_s3_post_wrapper()

        upload_info = self.s3_post_wrapper.generate_unprocessed_presigned_post_url(key=audio_clip.audio_file)

        return Response(
            data={
                'upload_url': upload_info['url'],
                'upload_fields': json.dumps(upload_info['fields']),
            },
            status=status.HTTP_200_OK
        )


    #checks if can start, but will not reset things if checking fails
    #returns None if can start, or Response if cannot
    #should ideally just return True/False and provide getCannotStartNormalisationResponse() for apis.py
    def start_normalisation(self, audio_clip_id:int)->None|Response:

        #doing "add normalisation to queue" here would cause circular import error, so we call at apis.py instead
        #get relevant records
        #we deal with db first, as cache is not intended for validation

        try:

            self.audio_clip = AudioClips.objects.select_related(
                'generic_status',
                'audio_clip_role',
            ).get(
                pk=audio_clip_id,
                user_id=self.user.id,
            )

            self.event = Events.objects.select_related(
                'generic_status',
            ).get(
                pk=self.audio_clip.event_id
            )

            #check if already processed
            #queue no longer exists when true
            #also more manageable than having frontend call "check status" API every time
            if self.audio_clip.generic_status.generic_status_name == 'ok':

                return Response(
                    data={
                        'is_processed': True,
                    },
                    status=status.HTTP_200_OK
                )

            #when responder is not done processing, queue will still exist
            if self.audio_clip.audio_clip_role.audio_clip_role_name == 'responder':

                self.event_reply_queue = EventReplyQueues.objects.get(
                    event_id=self.audio_clip.event_id,
                    locked_for_user=self.user,
                )

        except AudioClips.DoesNotExist:

            return Response(
                data={},
                status=status.HTTP_404_NOT_FOUND
            )

        except Events.DoesNotExist:

            return Response(
                data={},
                status=status.HTTP_404_NOT_FOUND
            )

        except EventReplyQueues.DoesNotExist:

            return Response(
                data={},
                status=status.HTTP_404_NOT_FOUND
            )

        #get cache first

        self._ensure_processing_cache_exists()

        #validate db rows, reset if cannot normalise

        can_normalise = self.check_db_can_normalise(
            audio_clip=self.audio_clip,
            event=self.event,
            event_reply_queue=self.event_reply_queue
        )

        processing_exists = self.processing_cache['processings'].get(str(self.audio_clip.id), None) is not None

        if can_normalise is False:

            #immediately delete processing if can no longer normalise

            if processing_exists is True:

                self.processing_cache['processings'].pop(str(self.audio_clip.id))

                self.set_processing_cache(self.processing_cache_key, self.processing_cache)

            return Response(
                data={},
                status=status.HTTP_404_NOT_FOUND
            )

        #determine processed upload_key from unprocessed
        #simply by switching extension

        determined_processed_upload_key = self.determine_processed_upload_key(
            self.audio_clip.audio_file,
            self.unprocessed_file_extensions,
            self.processed_file_extension
        )

        if determined_processed_upload_key == '':

            raise custom_error(
                ValueError,
                __name__,
                dev_message=f'''
                    Unprocessed file unexpectedly have processed extension.
                    AudioClips.id: {str(self.audio_clip.id)}
                '''
            )

        #check cache

        is_processing = self.processing_cache['processings'][str(self.audio_clip.id)]['is_processing']

        if processing_exists is True and is_processing is True:

            return Response(
                data={
                    "is_processing": True,
                    "attempts_left": self.processing_cache['processings'][str(self.audio_clip.id)]['attempts_left'],
                },
                status=status.HTTP_409_CONFLICT
            )

        #attempts_left will never be 0
        #cache will be deleted by task when done, be it on success, or 0 attempts_left on failure

        return None















