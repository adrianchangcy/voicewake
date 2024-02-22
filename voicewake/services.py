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

#Python libraries
from datetime import datetime, timezone, timedelta, tzinfo
from genericpath import isfile
from zoneinfo import ZoneInfo
from pydub import AudioSegment
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

#AWS
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

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

    #to format into queryset and/or sql-friendly format:
    #get_datetime_now().strftime('%Y-%m-%d %H:%M:%S %z')


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
                )
            )

            user_ids.append(user.id)
            event_ids.append(event.id)

    #create rows if they don't yet exist
    #ignore conflict because there's a decent chance that rows already exist, which is fine
    UserEvents.objects.bulk_create(
        bulk_user_events,
        ignore_conflicts=True
    )

    #do extra update for rows that already exist during bulk_create
    UserEvents.objects.filter(
        user=user,
        event_id__in=event_ids
    ).update(
        when_excluded_for_reply=datetime_now
    )


def prevent_events_from_showing_twice_at_front_page(user, events:list):

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
                )
            )

            user_ids.append(user.id)
            event_ids.append(event.id)

    #create rows if they don't yet exist
    #ignore conflict because there's a decent chance that rows already exist, which is fine
    UserEvents.objects.bulk_create(
        bulk_user_events,
        ignore_conflicts=True
    )

    #do extra update for rows that already exist during bulk_create
    UserEvents.objects.filter(
        user=user,
        event_id__in=event_ids
    ).update(
        when_seen_at_front_page=datetime_now
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

    error_message = "Invalid data."

    for key in serializer.errors:
        for first_error in serializer.errors[key]:
            return key + ": " + first_error

    return error_message


def copy_to_clipboard(full_string:str):

    #https://stackoverflow.com/a/17371323

    if platform.system() == 'Darwin':

        #Mac
        subprocess.run("pbcopy", text=True, input=full_string)

    else:

        subprocess.run("clip", text=True, input=full_string)


def output_testable_sql(full_sql, full_params):

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

    #for now, we only log errors that are meant for developers
    if dev_message != "":

        #find or create logger
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


def print_function_name(extra_stuff_to_print)->str:

    #this gives you outer function's name, i.e. not print_function_name()
    cframe = inspect.currentframe()
    calling_function_name = inspect.getframeinfo(cframe.f_back).function + "()"
    print("\n" + calling_function_name + ": " + str(extra_stuff_to_print) + "\n")



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
            if ((totp.t() > self.last_verified_counter) and (totp.verify(token, tolerance=self.token_validity_tolerance))):

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


    def guarantee_user_otp_instance(self):

        if self.user_otp_instance is None:

            self.user_otp_instance, created = UserOTP.objects.select_for_update().get_or_create(user=self.user_instance)


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


    def send_otp_email(self, recipient_email, subject, direction, otp):

        #we can freely use math.ceil() as long as TOTP_TOLERANCE_S is sufficient
        otp_expiry = settings.TOTP_VALIDITY_S / 60
        otp_expiry = str(math.ceil(otp_expiry))

        email_message = get_template('email/otp.html').render(context={
            'otp_direction': direction,
            'otp': otp,
            'otp_expiry': '%s minutes' % (otp_expiry),
            'cache_age': settings.CACHE_OTP_EMAIL_AGE_S,
        })

        send_mail(
            subject=subject,
            message='',
            html_message=email_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=True
        )

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
            #... --> frontend PUTs to pre-signed S3 URL --> when done, POST to backend --> ...
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
        self.is_ec2 = is_ec2
        self.allowed_unprocessed_file_extensions = allowed_unprocessed_file_extensions
        self.unprocessed_bucket_name = unprocessed_bucket_name
        self.s3_audio_file_max_size_b = s3_audio_file_max_size_b
        self.url_expiry_s = url_expiry_s
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


    def check_object_exists(self, key:str)->bool:

        try:

            #requires "s3:GetObject" and "s3:ListBucket" policy
            self.s3_client.head_object(
                Bucket=self.unprocessed_bucket_name,
                Key=key,
            )

            return True
        
        except ClientError as e:

            if e.response['ResponseMetadata']['HTTPStatusCode'] == 404:

                return False

            raise e


    def generate_unprocessed_object_key(self, user_id:int, file_extension:str):

        #frontend only records as mp4/webm, depending on browser

        if file_extension not in self.allowed_unprocessed_file_extensions:

            raise ValueError('Invalid file_extension. Must be one of: ' + str(self.allowed_unprocessed_file_extensions))

        datetime_now = get_datetime_now()

        #no starting slash
        #.format() converts args into str for us
        file_path = 'audio_clips/year_{0}/month_{1}/day_{2}/user_id_{3}/'.format(
            datetime_now.strftime('%Y'),
            datetime_now.strftime('%m'),
            datetime_now.strftime('%d'),
            user_id,
        )

        #if is_ec2=False, means from local, i.e. tests

        if self.is_ec2 is False:

            file_path = 'test/' + file_path

        #retry if full key exists

        for retry in range(0, self.key_exist_retries):

            #use secrets.token_hex() to mitigate wrongful possession from random guessing
            file_key = file_path + secrets.token_hex(16) + '.' + file_extension

            if self.check_object_exists(file_key) is False:

                return file_key

        raise ValueError('Maximum retries reached on check_object_exists().')


    def generate_presigned_post_url(self, key:str):

        #HTTP 422 on condition failure, will not upload
        #HTTP 204 on success
        #for file MimeType, e.g. allow only .mp3, must be done at bucket policy, not here
        #key will be available via upload_info['fields']['key']

        conditions = [
            {'bucket': self.unprocessed_bucket_name},
            {'key': key},
            ["starts-with", "$Content-Type", "audio/mp4,audio/webm"],
            ["content-length-range", 1024, self.s3_audio_file_max_size_b],
        ]

        try:

            return self.s3_client.generate_presigned_post(
                Bucket=self.unprocessed_bucket_name,
                Key=key,
                Fields={"Content-Type": "audio/mp4,audio/webm"},
                Conditions=conditions,
                ExpiresIn=self.url_expiry_s
            )

        except:

            raise custom_error(
                ValueError,
                __name__,
                dev_message=f"Couldn't generate POST URL for key: {key}",
                user_message='Upload is temporarily unavailable.'
            )


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
        region_name:str='',
        aws_access_key_id:str='',
        aws_secret_access_key:str='',
    ):

        self.is_ec2 = is_ec2
        self.region_name = region_name

        try:

            if is_ec2 is True:

                self.client = boto3.client(
                    service_name='lambda',
                    region_name=region_name,
                )

            else:

                self.client = boto3.client(
                    service_name='lambda',
                    region_name=region_name,
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
    ):

        payload = {
            's3_region_name': s3_region_name,
            'unprocessed_object_key': unprocessed_object_key,
            'processed_object_key': processed_object_key,
            'unprocessed_bucket_name': unprocessed_bucket_name,
            'processed_bucket_name': processed_bucket_name,
        }

        return self._invoke_lambda(
            function_name=os.environ['normalise_audio_clips'],
            payload=payload
        )



class AWSLambdaNormaliseAudioClips:

    #context
        #let backend API decide unprocessed and process keys
        #just accept both here
    #process
        #normalise --> copy to new bucket --> delete from old bucket --> return info
    #how to troubleshoot
        #do check=False, then get subprocess.run().stderr

    def __init__(
        self,
        is_lambda:bool,
        s3_region_name:str='',
        s3_aws_access_key_id:str='',
        s3_aws_secret_access_key:str='',
        unprocessed_object_key:str='',
        processed_object_key:str='',
        unprocessed_bucket_name:str='',
        processed_bucket_name:str='',
    ):

        self.is_lambda = is_lambda
        self.s3_region_name = s3_region_name
        self.unprocessed_object_key = unprocessed_object_key
        self.processed_object_key = processed_object_key
        self.unprocessed_bucket_name = unprocessed_bucket_name
        self.processed_bucket_name = processed_bucket_name

        if is_lambda is True:

            #with ffmpeg-arm64.zip/bin/ffmpeg, stored in S3, and loading as Layer in Lambda
            self.ffprobe_path = '/opt/bin/ffprobe'
            self.ffmpeg_path = '/opt/bin/ffmpeg'

        else:

            #with Windows environment variables
            self.ffprobe_path = 'ffprobe'
            self.ffmpeg_path = 'ffmpeg'

        #in the case of mp3, both codec and format/container are the same
        #mp3 can only choose 32000/44100/48000 sample rate
        #mp3 sample rate of 44100 and 48000 has big difference in quality with minimal size difference, as long as small
        self.desired_codec = "mp3"
        self.desired_format = "mp3"
        self.desired_sample_rate = "48k"

        #max timeout seconds for subprocess
        self.subprocess_timeout_s = 10

        #dBFS has max 0dB (loudest), min of approx. 6dB per bit, e.g. 16-bit will have 96dB floor
        # >0 will cause clipping
        #since we need 0 to 1 to draw peaks at frontend, but we don't know our floor (lack of bit depth info),
        #we assume via ffmpeg's silencedetect of default -60dB
        #update 2023-08-22: -60 is too high, with peaks near 1, so trying -99
        self.dbfs_floor = -99

        self.bucket_quantity = 20

        #other data
        self.audio_file = None
        self.audio_file_duration_s = None
        self.audio_volume_peaks = None

        #s3

        try:

            if is_lambda is True:

                self.s3_client = boto3.client(
                    service_name='s3',
                    region_name=s3_region_name,
                )

            else:

                self.s3_client = boto3.client(
                    service_name='s3',
                    region_name=s3_region_name,
                    aws_access_key_id=s3_aws_access_key_id,
                    aws_secret_access_key=s3_aws_secret_access_key,
                )

        except ClientError:

            raise


    def test_retrieve_unprocessed_audio_file_local(self, audio_file_path:str):

        with open(audio_file_path, 'rb+') as target_file:

            self.audio_file = target_file.read()


    def test_store_processed_audio_file_local(self, audio_file_path:str):

        with open(audio_file_path, 'w') as target_file_to_overwrite:

            target_file_to_overwrite.seek(0)

            for chunk in ContentFile(self.audio_file).chunks():

                #remove bytes starting from position 0
                target_file_to_overwrite.truncate(0)

                #write
                target_file_to_overwrite.write(chunk)


    def check_already_processed(self)->bool:

        try:

            #requires "s3:GetObject" and "s3:ListBucket" policy
            self.s3_client.head_object(
                Bucket=self.processed_bucket_name,
                Key=self.processed_object_key,
            )

            return True
        
        except ClientError as e:

            if e.response['ResponseMetadata']['HTTPStatusCode'] == 404:

                return False

            raise e


    def retrieve_unprocessed_audio_file(self):

        response = self.s3_client.get_object(
            Bucket=self.unprocessed_bucket_name,
            Key=self.unprocessed_object_key
        )

        #StreamingBody can only use .read() once, and does not contain .seek()
        #since our files are not large, we can load all into memory in this way
        self.audio_file = response['Body'].read()


    def prepare_info_before_normalise(self):

        #format
            #this gets all keys, compared to 'format=duration', which returns only duration

        result = subprocess.run(
            [
                self.ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format',
                '-show_streams',
                '-select_streams', 'a',
                '-of', 'json',
                '-i', 'pipe:0',
            ],
            input=self.audio_file,
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file_info = json.loads(result.stdout)

        #validate everything
        self._validate_info_before_normalise()


    def _validate_info_before_normalise(self):

        if self.audio_file_info is None:

            raise ValueError('No self.audio_file_info to validate.')
        
        #audio_file_info['streams'] can have multiple dicts if there's not only audio in it
        #e.g. a flac file from an album for test has a jpeg in it with ['index'] == 1
        #don't know whether the index order is always fixed, hence the loop

        #we don't care about codec
        #we have "-select_streams a" to tell us that no audio stream exists
        if len(self.audio_file_info['streams']) == 0:

            raise ValueError('No audio stream found.')


    def normalise_and_overwrite_audio_file(self):

        #"loudnorm=I=-16:TP=-1.5:LRA=11" is from loudnorm docs on EBU R 128
        #"loudnorm=I=-23:LRA=7:TP=-2" is from ffmpeg-normalize on EU's LUFS -23 regulation
        loudnorm_args = "loudnorm=I=-23:TP=-2:LRA=7"

        #I is LUFS
        #LRA is loudness range, i.e. range between softest and loudest parts
        #TP is true peak, -2 seems common, just be sure to give enough headroom towards 0, and never over 0

        #first pass, get measurement
        ffmpeg_cmd = subprocess.run(
            [
                self.ffmpeg_path,
                "-i", "pipe:0",
                "-af", loudnorm_args + ":print_format=json",
                '-f', "null", "/dev/null"
            ],
            input=self.audio_file,
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        #get print string from stderr
        first_pass_data = ffmpeg_cmd.stderr.decode()

        #construct our json string
        #this will work as long as entire print string only has one {}
        first_pass_dict = re.search(r"(\{[\s\S]*\})", first_pass_data)[0]

        if first_pass_dict is None:

            raise ValueError("Regex could not find the data needed for first_pass_dict")

        #transform into proper dict
        first_pass_dict = json.loads(first_pass_dict)
        first_pass_dict = dict(first_pass_dict)

        #prepare -af values for second pass
        #can't directly .format() here, must call the variable again
        ffmpeg_cmd_af = loudnorm_args +\
            ":measured_I={0}" +\
            ":measured_LRA={1}" +\
            ":measured_TP={2}" +\
            ":measured_thresh={3}" +\
            ":offset={4}" +\
            ":linear=true:print_format=summary"
        
        ffmpeg_cmd_af = ffmpeg_cmd_af.format(
            first_pass_dict["input_i"],
            first_pass_dict["input_lra"],
            first_pass_dict["input_tp"],
            first_pass_dict["input_thresh"],
            first_pass_dict["target_offset"]
        )
        
        #do second pass, get file
        ffmpeg_cmd = subprocess.run(
            [
                self.ffmpeg_path,
                "-i", "pipe:0",
                "-af", ffmpeg_cmd_af,
                "-ar", self.desired_sample_rate,           #sample rate; mp3 can only choose 32000/44100/48000
                # "-b:a", "124k",         #bit rate, not sure if safe/redundant/necessary
                "-c:a", self.desired_codec,          #codec; a is audio, v is video
                "-f", self.desired_format, "pipe:1"   #f is format; for disk files, can just write "my_folder/file.mp3"
            ],
            input=self.audio_file,
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file = ffmpeg_cmd.stdout


    def get_duration_after_normalise(self):

        #we have to do this only after passing through ffmpeg, e.g. normalisation
        #otherwise, some original files will error when seeking via '-read_intervals' and arbitary '999999'

        #'-show_packets', '-read_intervals' + '999999'
            #for file duration, getting from packets is more reliable than metadata such as format=duration:
            #guarantee that -read_intervals, in seconds, is >= file duration, via arbitrarily large value
            #absolute single value will become absolute start position, so start from last packet
            #will fall back to last packet when value is too big
            #this is better than loading all packets into memory just to get [-1]
        #format
            #this gets all keys, compared to 'format=duration', which returns only duration
        #'-show_entries', 'format'
            #not affected by us skipping packets via -read_intervals

        result = subprocess.run(
            [
                self.ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format',
                '-show_packets',
                '-read_intervals', '999999',
                '-show_streams',
                '-select_streams', 'a',
                '-of', 'json',
                '-i', 'pipe:0',
            ],
            input=self.audio_file,
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        audio_file_info = json.loads(result.stdout)

        try:

            #determine audio_file_duration_s via last packet's pts_time
            #round off duration to int, floor is preferred for frontend slider
            self.audio_file_duration_s = math.floor(
                float(audio_file_info['packets'][-1]['pts_time'])
            )

        except:

            raise ValueError('Could not determine duration of file uploaded.')


    def get_peaks_by_buckets(self) -> list[float]:

        #call this after normalisation

        #get duration
        #get sample rate
        #asetnsamples = (duration / x buckets) * sample rate
        #expect x + 1 buckets output, so compare second last and last bucket and select the one with higher peak

        #to get highest peak per x, add "asetnsamples=x" after amovie, i.e. chunk size, e.g. "amovie=...,asetnsamples=x,..."
        #e.g. if file is 48000Hz frequency, i.e. 48000 samples/sec, asetnsamples=48000 gives you 1 sec/bucket

        #get necessary info
        sample_rate = int(self.audio_file_info['streams'][0]['sample_rate'])

        #calculate appropriate sample rate to get bucket_quantity + 1
        #math.floor() is important to guarantee we always get surplus buckets, i.e. just compare last buckets
        #compared to math.ceil(), which may give us less buckets than we need, i.e. must maybe create last fake bucket
        asetnsamples = math.floor(self.audio_file_duration_s / self.bucket_quantity * sample_rate)
        
        #must escape ":"
        ffprobe_i = 'amovie=pipe\\\\:0,asetnsamples=%s,astats=metadata=1:reset=1' % (str(asetnsamples))

        #get peaks
        result = subprocess.run(
            [
                self.ffprobe_path,
                '-v', 'error',
                '-f', 'lavfi',
                '-i', ffprobe_i,
                '-show_entries', 'frame_tags=lavfi.astats.Overall.Peak_level',
                '-of', 'json'
            ],
            input=self.audio_file,
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        result = json.loads(result.stdout)

        #extract peaks
        audio_volume_peaks = []

        for count in range(self.bucket_quantity):

            #we fill the bucket to full first, then use last stored bucket to evaluate extra buckets
            peak_to_store = 0

            #value is in dBFS, max 0, min is approx. 6dB per bit depth
            #so bigger negative value means more quiet
            peak_to_store = float(result['frames'][count]['tags']['lavfi.astats.Overall.Peak_level'])

            #prevent exceeding floor
            if peak_to_store < self.dbfs_floor:

                peak_to_store = self.dbfs_floor

            #should never have > 0dB (will produce audio clipping)
            if peak_to_store > 0:
                
                raise ValueError('Audio normalisation had failed, as there were above 0dBFS peaks detected.')

            #get percentage
            # -x / -y will always be positive
            peak_to_store = peak_to_store / self.dbfs_floor

            #invert percentage
            peak_to_store = 1 - peak_to_store

            #get 0 to 1 value
            peak_to_store = peak_to_store * 1

            #truncate
            peak_to_store = float(round(peak_to_store, 2))

            #while audio_volume_peaks is not yet full, fill until full
            if count < self.bucket_quantity:

                audio_volume_peaks.append(peak_to_store)
                continue

            #handle extra buckets
            #store the higher peak between last stored peak and current peak
            if audio_volume_peaks[self.bucket_quantity] < peak_to_store:

                audio_volume_peaks[self.bucket_quantity] = peak_to_store

        self.audio_volume_peaks = audio_volume_peaks

        return audio_volume_peaks


    def store_processed_audio_file(self):

        return self.s3_client.put_object(
            Bucket=self.processed_bucket_name,
            Key=self.processed_object_key,
            Body=self.audio_file
        )


    def delete_unprocessed_audio_file(self):

        return self.s3_client.delete_object(
            Bucket=self.unprocessed_bucket_name,
            Key=self.unprocessed_object_key,
        )


    def create_return_response(self, error_object=None):

        #error_object is ClientError

        response = {
            'lambda_status_code': 200,
            'lambda_message': '',
            'audio_volume_peaks': self.audio_volume_peaks,
            'audio_duration_s': self.audio_file_duration_s
        }

        if error_object is not None:

            response['lambda_status'] = error_object.response['ResponseMetadata']['HTTPStatusCode']
            response['lambda_message'] = error_object.response['Error']['Message']

        return response


    def main(self):

        response = self.create_return_response()

        try:

            if self.check_already_processed() is True:

                return response

            self.retrieve_unprocessed_audio_file()
            self.prepare_info_before_normalise()
            self.normalise_and_overwrite_audio_file()
            self.get_duration_after_normalise()
            self.get_peaks_by_buckets()
            self.store_processed_audio_file()

        except ClientError as e:

            return self.create_return_response(e)

        return response



class CreateAudioClips():

    #this is step 1
    #user POSTs to here --> create "processing" audio_clip and/or event --> return presigned URL and other fields

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


    def get_cooldown_on_audio_clip_create_limit_s(self)->int:

        #this is for "X max new posts every __", which in this case is every 24h

        datetime_checkpoint = self.datetime_now.strftime('%Y-%m-%d 00:00:00.%f %z')
        datetime_checkpoint_raw = datetime.strptime(datetime_checkpoint, '%Y-%m-%d %H:%M:%S.%f %z')

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
            when_created__gte=datetime_checkpoint,
            audio_clip_role__audio_clip_role_name=audio_clip_role_name
        ).count()

        if the_count < count_limit:

            return 0

        #get next 00:00:00 day, and get difference from now
        pretty_difference_s = ((datetime_checkpoint_raw + timedelta(days=1)) - self.datetime_now).total_seconds()

        return math.ceil(pretty_difference_s)


    def _get_event_reply_queue(self, event_id:int):

        try:

            self.event_reply_queue = EventReplyQueues.objects.select_for_update(
                of=("self",)
            ).select_related(
                'event__generic_status'
            ).get(
                event_id=event_id,
                locked_for_user=self.user
            )

        except EventReplyQueues.DoesNotExist:

            raise custom_error(
                ValueError,
                __name__,
                user_message='Unable to reply to this event.'
            )


    def _check_user_can_create_reply(self)->bool:

        if self.event_reply_queue is None:

            raise custom_error(
                ValueError,
                __name__,
                dev_message="EventReplyQueue not yet retrieved. Call self._get_event_reply_queue()."
            )

        #deny if not yet replying
        if self.event_reply_queue.is_replying is False:

            return False

        #is replying, proceed

        #check that event is still ok
        if self.event_reply_queue.event.generic_status.generic_status_name != 'incomplete':

            #remove expired reply choice
            self.event_reply_queue.delete()
            self.event_reply_queue = None

            return False

        #check for expiry
        if(
            self.event_reply_queue.when_locked <
            (self.datetime_now - timedelta(seconds=self.event_reply_expiry_seconds))
        ):

            #remove expired reply choice
            self.event_reply_queue.delete()
            self.event_reply_queue = None

            return False

        return True


    def _get_records_for_normalise(self, audio_clip_id:int):

        try:

            self.audio_clip = AudioClips.objects.select_related(
                'generic_status',
                'audio_clip_role',
            ).get(
                pk=audio_clip_id,
                user_id=self.user.id,
            )

            self.event = Events.objects.select_related('generic_status',).get(pk=self.audio_clip.event_id)

        except AudioClips.DoesNotExist:

            raise custom_error(
                ValueError,
                __name__,
                user_message='Recording does not exist.',
            )

        except Events.DoesNotExist:

            raise custom_error(
                ValueError,
                __name__,
                user_message='Event does not exist.',
            )


    def _determine_processed_upload_key(self, unprocessed_upload_key:str)->str:

        #we simply swap the extension of unprocessed_upload_key
        #we don't have to do detailed string checks
            #will compare directly with AudioClips.audio_file for validation

        processed_upload_key = ''

        for file_extension in self.unprocessed_file_extensions:

            unprocessed_upload_key_extension = unprocessed_upload_key[
                -len(file_extension):len(unprocessed_upload_key)
            ]

            if unprocessed_upload_key_extension == file_extension:

                processed_upload_key = unprocessed_upload_key[0:-len(file_extension)]

                processed_upload_key += self.processed_file_extension

                return processed_upload_key

        raise custom_error(
            ValueError,
            __name__,
            dev_message='upload_key ' + unprocessed_upload_key + ' is not ' + str(self.unprocessed_file_extensions),
            user_message='Invalid upload_key.'
        )


    def _check_can_normalise(
        self,
        unprocessed_upload_key:str,
        determined_processed_upload_key:str,
    )->bool:

        if self.audio_clip is None or self.event is None:

            raise custom_error(
                ValueError,
                __name__,
                dev_message="Missing records. Call self._get_records_for_normalise()."
            )

        #don't have to check if audio_clip belongs to user
        #since this is handled at self.get_records_for_normalise()

        #check event

        if (
            (
                self.current_context == 'create_event' and
                self.event.generic_status.generic_status_name == 'processing'
            ) or (
                self.current_context == 'create_reply' and
                self.event.generic_status.generic_status_name == 'incomplete'
            )
        ):

            pass

        else:

            raise custom_error(
                ValueError,
                __name__,
                user_message='This event is unavailable.',
            )

        #check audio_clip

        if (
            self.audio_clip.user.id == self.user.id and
            self.audio_clip.generic_status.generic_status_name == 'processing' and
            self.audio_clip.audio_duration_s == 0 and
            len(self.audio_clip.audio_file) == 0 and
            len(self.audio_clip.audio_volume_peaks) == 0 and
            self.audio_clip.audio_file == unprocessed_upload_key
        ):

            #ready to process
            return True

        elif (
            self.audio_clip.user.id == self.user.id and
            self.audio_clip.generic_status.generic_status_name == 'ok' and
            self.audio_clip.audio_duration_s > 0 and
            len(self.audio_clip.audio_file) > 0 and
            len(self.audio_clip.audio_volume_peaks) > 0 and
            self.audio_clip.audio_file == determined_processed_upload_key
        ):

            #already processed
            return False

        else:

            raise custom_error(
                ValueError,
                __name__,
                user_message='This recording could not be processed.',
            )


    def _initialise_s3_post_wrapper(self):

        self.s3_post_wrapper = S3PostWrapper(
            is_ec2=self.is_ec2,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B'],
            url_expiry_s=os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S'],
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )


    def _initialise_lambda_wrapper(self):

        self.lambda_wrapper = AWSLambdaWrapper(
            is_ec2=self.is_ec2,
            region_name=os.environ['AWS_LAMBDA_REGION_NAME'],
            aws_access_key_id=os.environ['AWS_LAMBDA_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_LAMBDA_SECRET_ACCESS_KEY'],
        )


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
                dev_message="Invalid current_context."
            )

        #perform checks

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

        #create event, as "processing"
        self.event = Events.objects.create(
            event_name=event_name,
            generic_status=generic_status_processing,
            created_by=self.user,
        )

        #create audio_clip, as "processing"
        #we update audio_volume_peaks, audio_duration_s, and audio_file later
        self.audio_clip = AudioClips.objects.create(
            user=self.user,
            audio_clip_role=audio_clip_role,
            audio_clip_tone=audio_clip_tone,
            event=self.event,
            audio_volume_peaks=[],
            audio_duration_s=0,
            audio_file='',
            generic_status=generic_status_processing
        )

        #s3

        self._initialise_s3_post_wrapper()

        #generate key and presigned URL

        upload_key = self.s3_post_wrapper.generate_unprocessed_object_key(
            user_id=self.user.id,
            file_extension=recorded_file_extension
        )

        upload_info = self.s3_post_wrapper.generate_presigned_post_url(key=upload_key)

        #save key as audio_file
        #currently has file extension of unprocessed file
        self.audio_clip.audio_file = upload_key
        self.audio_clip.save()

        return Response(
            data={
                'data': {
                    'upload_url': upload_info['url'],
                    'upload_fields': json.dumps(upload_info['fields']),
                    'audio_clip_id': self.audio_clip.id,
                    'unprocessed_upload_key': upload_key,
                }
            },
            status=status.HTTP_201_CREATED
        )


    def create_records_and_return_s3_endpoint_as_responder(
        self,
        event_id:int,
        audio_clip_tone_id:int,
        recorded_file_extension:str,
    )->Response:

        if self.current_context != "create_reply":

            raise custom_error(
                ValueError,
                __name__,
                dev_message="Invalid current_context."
            )

        #get queue

        self._get_event_reply_queue(event_id)

        #perform checks

        if self._check_user_can_create_reply() is False:

            return Response(
                data={
                    'data': {
                        'message': 'This event can no longer be replied to.',
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #no need to check for daily reply limit here
        #as that is enforced when listing choices

        #can reply, proceed

        audio_clip_role = AudioClipRoles.objects.get(audio_clip_role_name='responder')
        audio_clip_tone = AudioClipTones.objects.get(pk=audio_clip_tone_id)
        generic_status_processing = GenericStatuses.objects.get(generic_status_name='processing')

        self.audio_clip = AudioClips.objects.create(
            user=self.user,
            audio_clip_role=audio_clip_role,
            audio_clip_tone=audio_clip_tone,
            event_id=event_id,
            audio_volume_peaks=[],
            audio_duration_s=0,
            audio_file='',
            generic_status=generic_status_processing
        )

        #s3

        self._initialise_s3_post_wrapper()

        #generate key and presigned URL

        upload_key = self.s3_post_wrapper.generate_unprocessed_object_key(
            user_id=self.user.id,
            file_extension=recorded_file_extension
        )

        upload_info = self.s3_post_wrapper.generate_presigned_post_url(key=upload_key)

        #save key as audio_file
        #currently has file extension of unprocessed file
        self.audio_clip.audio_file = upload_key
        self.audio_clip.save()

        return Response(
            data={
                'data': {
                    'upload_url': upload_info['url'],
                    'upload_fields': json.dumps(upload_info['fields']),
                    'audio_clip_id': self.audio_clip.id,
                    'unprocessed_upload_key': upload_key,
                }
            },
            status=status.HTTP_201_CREATED
        )


    def normalise_and_update_records(
        self,
        audio_clip_id:int,
        unprocessed_upload_key:str,
    )->Response:

        #get records, particularly AudioClips and Events

        self._get_records_for_normalise(audio_clip_id)

        #determine processed upload_key from unprocessed
        #simply by switching extension

        determined_processed_upload_key = self._determine_processed_upload_key(unprocessed_upload_key)

        #check whether can normalise

        can_normalise = self._check_can_normalise(
            unprocessed_upload_key=unprocessed_upload_key,
            determined_processed_upload_key=determined_processed_upload_key
        )

        if can_normalise is False:

            return Response(
                data={
                    "message": "Recording was successfully processed.",
                },
                status=status.HTTP_201_CREATED
            )

        #no need to check event_reply_queue,
        #since most cases would call this directly after part 1, and part 1 does check it
        #also, Celery tasks will still check it for us

        #call Lambda to normalise and transfer file to processed bucket

        self._initialise_lambda_wrapper()

        #refer to AWSLambdaNormaliseAudioClips.create_return_response()
        #when ok, will always return 200
        lambda_response_data = self.lambda_wrapper.invoke_normalise_audio_clips_lambda(
            s3_region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_object_key=unprocessed_upload_key,
            processed_object_key=determined_processed_upload_key,
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            processed_bucket_name=os.environ['AWS_S3_MEDIA_BUCKET_NAME'],
        )

        #validate lambda response

        serializer = AWSLambdaNormaliseAudioClipsAPISerializer(data=lambda_response_data, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': 'Unable to process your recording. Try again later.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        lambda_response_data = serializer.validated_data

        if lambda_response_data['lambda_status_code'] != 200:

            return Response(
                data={
                    "message": "Unable to process your recording. Try again later.",
                },
                status=lambda_response_data['lambda_status_code']
            )

        #ok, proceed

        generic_status_ok = GenericStatuses.objects.get(generic_status_name='ok')

        #update audio_clip

        self.audio_clip.audio_duration_s = lambda_response_data['audio_duration_s']
        self.audio_clip.audio_volume_peaks = lambda_response_data['audio_volume_peaks']
        self.audio_clip.audio_file = determined_processed_upload_key
        self.audio_clip.generic_status = generic_status_ok

        self.audio_clip.save()

        #if originator, update event from 'processing' to 'incomplete'
        #if responder, update event from 'incomplete' to 'completed'

        if self.audio_clip.audio_clip_role.audio_clip_role_name == 'originator':

            self.event.generic_status = GenericStatuses.objects.get(generic_status_name='incomplete')

        elif self.audio_clip.audio_clip_role.audio_clip_role_name == 'responder':

            self.event.generic_status = GenericStatuses.objects.get(generic_status_name='completed')

            #remove event_reply_queue
            self._get_event_reply_queue(self.event.id)
            self.event_reply_queue.delete()
            self.event_reply_queue = None

        else:

            raise custom_error(
                ValueError,
                __name__,
                dev_message='Unrecognised audio_clip.audio_clip_role.audio_clip_role_name.',
                user_message='Something went wrong. Try again later.'
            )

        self.event.save()

        return Response(
            data={
                "message": "Recording was successfully uploaded.",
            },
            status=status.HTTP_201_CREATED
        )





















