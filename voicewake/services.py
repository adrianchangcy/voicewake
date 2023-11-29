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

#app files
from .models import *



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

    #we sometimes have EventReplyQueues on an each-audio-clip basis, while sometimes on each-event basis
    #we choose each-event basis

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


def output_testable_sql(full_sql, full_params):

    with connection.cursor() as cursor:

        print(
            cursor.mogrify(
                full_sql,
                full_params
            )
        )


#not advisable to group functions via class,
#it's better to create modules (files) to group functions together
def custom_error(error_class:Exception, dev_message="", user_message="")->Exception:

    #demo
    # try:
    #     raise custom_error(ValueError, "yo fix this", "hehe oops")
    # except ValueError as e:
    #     print(get_user_message_from_custom_error(e))

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



class PrepareTestData:

    #we don't use hours_ago parameter
    #because our models use auto_now_add, which cannot be overriden
    #too lazy to replace auto_now_add=True with default=get_datetime_now(), since only tests would currently justify this
    def __init__(self, for_test:bool=True, audio_clip_tone_slug=''):

        #FYI, when running tests, settings.DEBUG is False
        if settings.DEBUG is True or for_test is True:
            
            pass

        else:

            raise RuntimeError('You cannot use PrepareTestData when settings.DEBUG is not True.')

        #ensure minimum 10 users

        user_count = get_user_model().objects.all().count()

        if user_count < 10:

            for x in range(user_count, 10):

                email = 'user' + str(x) + '@gmail.com'
                username = 'useR' + str(x)

                get_user_model().objects.create_user(
                    email=email,
                    username=username
                )

        self.bulk_users = get_user_model().objects.all()[0:10]
        self.default_originator = self.bulk_users[0]
        self.default_responder = self.bulk_users[1]

        self.audio_file = "/audio_test.mp3"
        self.audio_volume_peaks = [
            0.32, 0.47, 0.76, 0.75, 0.79, 0.59, 0.78, 0.83, 0.85, 0.77,
            0.62, 0.69, 0.97, 0.96, 0.97, 0.96, 0.96, 0.63, 0.47, 0.0
        ]
        self.audio_duration_s = 26
        self.datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))
        self.audio_clip_role_originator = AudioClipRoles.objects.get(audio_clip_role_name='originator')
        self.audio_clip_role_responder = AudioClipRoles.objects.get(audio_clip_role_name='responder')
        self.generic_status_ok = GenericStatuses.objects.get(generic_status_name='ok')
        self.generic_status_incomplete = GenericStatuses.objects.get(generic_status_name='incomplete')
        self.generic_status_completed = GenericStatuses.objects.get(generic_status_name='completed')

        if audio_clip_tone_slug != '':

            self.audio_clip_tone = AudioClipTones.objects.get(audio_clip_tone_slug=audio_clip_tone_slug)

        else:

            self.audio_clip_tone = AudioClipTones.objects.first()


    def create_incomplete_events(self, originator, quantity=0):

        #incomplete

        incomplete_count = quantity

        bulk_events = []
        bulk_originator_audio_clips = []

        #events

        for x in range(0, incomplete_count):

            event_name = "incomplete #" + str(x) + " by " + originator.username

            bulk_events.append(Events(
                event_name=event_name,
                created_by=originator,
                generic_status=self.generic_status_incomplete,
            ))

            print('Processing #' + str(x) + ' bulk_events')
        
        bulk_events = Events.objects.bulk_create(bulk_events)

        #audio_clips

        for x in range(0, incomplete_count):

            bulk_originator_audio_clips.append(AudioClips(
                user=originator,
                audio_clip_role=self.audio_clip_role_originator,
                audio_file=self.audio_file,
                audio_volume_peaks=self.audio_volume_peaks,
                audio_duration_s=self.audio_duration_s,
                generic_status=self.generic_status_ok,
                event=bulk_events[x],
                audio_clip_tone=self.audio_clip_tone
            ))

            print('Processing #' + str(x) + ' bulk_originator_audio_clips')

        bulk_originator_audio_clips = AudioClips.objects.bulk_create(bulk_originator_audio_clips)

        #update when_created

        random_days = random.randrange(0, 30)
        target_datetime = get_datetime_now() - timedelta(days=random_days)

        for x in range(0, incomplete_count):

            if x % 10 == 0:

                random_days = random.randrange(0, 30)
                target_datetime = get_datetime_now() - timedelta(days=random_days)

            bulk_events[x].when_created = target_datetime
            bulk_events[x].last_modified = target_datetime

            bulk_originator_audio_clips[x].when_created = target_datetime
            bulk_originator_audio_clips[x].last_modified = target_datetime

            print('Processing #' + str(x) + ' bulk_events, bulk_originator_audio_clips')

        Events.objects.bulk_update(bulk_events, ['when_created', 'last_modified'])
        AudioClips.objects.bulk_update(bulk_originator_audio_clips, ['when_created', 'last_modified'])

        #likes/dislikes

        is_liked_options = [True, False]
        bulk_audio_clip_likes_dislikes = []

        for x in range(0, incomplete_count):

            for user in self.bulk_users:

                is_liked_roll = random.randrange(0, 3)

                if is_liked_roll == 2:

                    #skip if out of range for is_liked_options, i.e. null, no point inserting
                    continue

                bulk_audio_clip_likes_dislikes.append(
                    AudioClipLikesDislikes(
                        user=user,
                        audio_clip=bulk_originator_audio_clips[x],
                        is_liked=is_liked_options[is_liked_roll]
                    )
                )

            print('Processing #' + str(x) + ' bulk_audio_clip_likes_dislikes')

        AudioClipLikesDislikes.objects.bulk_create(bulk_audio_clip_likes_dislikes)


    def create_completed_events(self, originator, responder, quantity=0):

        #completed

        completed_count = quantity

        bulk_events = []
        bulk_originator_audio_clips = []
        bulk_responder_audio_clips = []

        #events

        for x in range(0, completed_count):

            event_name = "completed #" + str(x) + " by " + originator.username

            bulk_events.append(Events(
                event_name=event_name,
                created_by=originator,
                generic_status=self.generic_status_completed,
            ))

            print('Processing #' + str(x) + ' bulk_events')
        
        bulk_events = Events.objects.bulk_create(bulk_events)

        #audio_clips

        for x in range(0, completed_count):

            bulk_originator_audio_clips.append(AudioClips(
                user=originator,
                audio_clip_role=self.audio_clip_role_originator,
                audio_file=self.audio_file,
                audio_volume_peaks=self.audio_volume_peaks,
                audio_duration_s=self.audio_duration_s,
                generic_status=self.generic_status_ok,
                event=bulk_events[x],
                audio_clip_tone=self.audio_clip_tone
            ))

            bulk_responder_audio_clips.append(AudioClips(
                user=responder,
                audio_clip_role=self.audio_clip_role_responder,
                audio_file=self.audio_file,
                audio_volume_peaks=self.audio_volume_peaks,
                audio_duration_s=self.audio_duration_s,
                generic_status=self.generic_status_ok,
                event=bulk_events[x],
                audio_clip_tone=self.audio_clip_tone
            ))

            print('Processing #' + str(x) + ' bulk_originator_audio_clips, bulk_responder_audio_clips')

        bulk_originator_audio_clips = AudioClips.objects.bulk_create(bulk_originator_audio_clips)
        bulk_responder_audio_clips = AudioClips.objects.bulk_create(bulk_responder_audio_clips)

        #update when_created

        random_days = random.randrange(0, 30)
        target_datetime = get_datetime_now() - timedelta(days=random_days)

        for x in range(0, completed_count):

            if x % 10 == 0:

                random_days = random.randrange(0, 30)
                target_datetime = get_datetime_now() - timedelta(days=random_days)

            bulk_events[x].when_created = target_datetime
            bulk_events[x].last_modified = target_datetime

            bulk_originator_audio_clips[x].when_created = target_datetime
            bulk_originator_audio_clips[x].last_modified = target_datetime

            bulk_responder_audio_clips[x].when_created = target_datetime
            bulk_responder_audio_clips[x].last_modified = target_datetime

            print('Processing #' + str(x) + ' bulk_events, bulk_originator_audio_clips, bulk_responder_audio_clips')

        Events.objects.bulk_update(bulk_events, ['when_created', 'last_modified'])
        AudioClips.objects.bulk_update(bulk_originator_audio_clips, ['when_created', 'last_modified'])
        AudioClips.objects.bulk_update(bulk_responder_audio_clips, ['when_created', 'last_modified'])

        #likes/dislikes

        is_liked_options = [True, False]
        bulk_audio_clip_likes_dislikes = []

        for x in range(0, completed_count):

            for user in self.bulk_users:

                is_liked_roll = random.randrange(0, 3)

                if is_liked_roll == 2:

                    #skip if out of range for is_liked_options, i.e. null, no point inserting
                    continue

                bulk_audio_clip_likes_dislikes.append(
                    AudioClipLikesDislikes(
                        user=user,
                        audio_clip=bulk_originator_audio_clips[x],
                        is_liked=is_liked_options[is_liked_roll]
                    )
                )

            print('Processing #' + str(x) + ' bulk_audio_clip_likes_dislikes')

        AudioClipLikesDislikes.objects.bulk_create(bulk_audio_clip_likes_dislikes)


    def with_existing_events_queue_reply_choices(self, quantity=0):

        target_count = quantity

        bulk_incomplete_events = Events.objects.filter(
            generic_status__generic_status_name='incomplete'
        )[0:target_count]

        list(bulk_incomplete_events)

        datetime_now = get_datetime_now()
        bulk_event_reply_queues = []

        for x, event in enumerate(bulk_incomplete_events):

            when_locked = datetime_now - timedelta(minutes=random.randrange(1, settings.EVENT_REPLY_CHOICE_EXPIRY_SECONDS*2))

            #ensure full datetime logic consistency
            if when_locked < event.when_created:

                when_locked = event.when_created

            #ensure that users don't reply to their own events
            random_responder = self.bulk_users[random.randrange(0, len(self.bulk_users))]

            while random_responder.id == event.created_by.id:

                random_responder = self.bulk_users[random.randrange(0, len(self.bulk_users))]

            bulk_event_reply_queues.append(
                EventReplyQueues(
                    event=event,
                    when_locked=when_locked,
                    locked_for_user=random_responder,
                    is_replying=False
                )
            )

            print('Processing #' + str(x) + ' bulk_event_reply_queues')

        EventReplyQueues.objects.bulk_create(bulk_event_reply_queues)


    def with_existing_events_confirm_reply_choice(self):

        #must first queue from with_existing_events_queue_reply_choice()
        EventReplyQueues.objects.update(is_replying=True)


    def delete_all_event_reply_queues(self):

        #does not affect Events
        #provide this so that next with_existing_events_queue_reply_choices() call has no conflicts
        EventReplyQueues.objects.all().delete()


    def quick_start(self):

        for x in range(0, len(self.bulk_users)):

            self.create_incomplete_events(
                self.bulk_users[x],
                random.randrange(400, 800)
            )

            if x == len(self.bulk_users) - 1:

                break

            self.create_completed_events(
                self.bulk_users[x],
                self.bulk_users[x+1],
                random.randrange(700, 1400)
            )

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

        #we can freely use math.ceil() as long as TOTP_TOLERANCE_SECONDS is sufficient
        otp_expiry = settings.TOTP_VALIDITY_SECONDS / 60
        otp_expiry = str(math.ceil(otp_expiry))

        email_message = get_template('email/otp.html').render(context={
            'otp_direction': direction,
            'otp': otp,
            'otp_expiry': '%s minutes' % (otp_expiry)
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



class HandleAudioFile:

    def __init__(self, audio_file:Union[InMemoryUploadedFile, TemporaryUploadedFile], overwrite_source:bool):

        #we do not accept abs path, because our code overrides the passed file to save memory
        #i.e. InMemoryUploadedFile/TemporaryUploadedFile makes .save() go smoothly
        #preventing override would mean duplicating memory/disk space, and ensuring disk copy is deleted
        if overwrite_source is False:

            raise custom_error(
                ValueError,
                dev_message="Current code will always overwrite original source's bytes to save memory."
            )

        #precaution:
            #size is checked via .size at serializer/form, not here
            #if you pass absolute path, remember to call .close_audio_file()

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

        #check type
        if type(audio_file) not in [InMemoryUploadedFile, TemporaryUploadedFile]:

            raise custom_error(
                ValueError,
                dev_message="audio_file must be of type [InMemoryUploadedFile, TemporaryUploadedFile]."
            )
        
        # if type(audio_file) == str:
            # self.audio_file = open(audio_file, "rb+")

        self.audio_file = audio_file

        #other data
        self.audio_file_duration_s = None
        self.peak_buckets = None


    def prepare_audio_file_info(self)->bool:

        self.audio_file.seek(0)

        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format',  #if you want only some keys, do format=duration, no difference though
                '-show_streams',
                '-select_streams', 'a',
                '-of', 'json',
                '-i', 'pipe:0'
            ],
            input=self.audio_file.read(),
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file.seek(0)

        self.audio_file_info = json.loads(result.stdout)

        if 'duration' in self.audio_file_info['format']:

            #has duration metadata
            #round off duration to int, floor is preferred in terms of presentation
            self.audio_file_duration_s = math.floor(
                float(self.audio_file_info['format']['duration'])
            )

        else:

            #no duration metadata, get it from packets instead
            self._get_duration_from_last_packet()

        #validate everything
        self._validate_audio_file_info()

        return True


    def _get_duration_from_last_packet(self):

        #dts_time: DTS time, decides when a frame has to be decoded
        #pts_time: PTS time, describes when a frame has to be presented
        #difference only becomes important in video B-frames, i.e. frames containing references past + future frames

        self.audio_file.seek(0)

        #expect packets to have dts_time/pts_time
        #we get last packet and use pts_time as seemingly accurate total duration in seconds
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-show_packets',
                '-of', 'json',
                '-read_intervals', '999999',    #seconds, make sure is longer than file duration, 999999 is safe
                '-i', 'pipe:0',
            ],
            input=self.audio_file.read(),
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file.seek(0)

        result = json.loads(result.stdout)

        #round off duration to int, floor is preferred in terms of presentation
        self.audio_file_duration_s = math.floor(
            float(result['packets'][0]['pts_time'])
        )


    def _validate_audio_file_info(self)->bool:

        if self.audio_file_info is None:

            raise custom_error(
                ValueError,
                dev_message="Cannot validate audio_file_info when it is None."
            )
        
        #audio_file_info['streams'] can have multiple dicts if there's not only audio in it
        #e.g. a flac file from an album for test has a jpeg in it with ['index'] == 1
        #don't know whether the index order is always fixed, hence the loop

        #we don't care about codec
        #we have "-select_streams a" to tell us that no audio stream exists
        if len(self.audio_file_info['streams']) == 0:

            raise custom_error(
                ValueError,
                dev_message="File does not contain audio.",
                user_message="File does not contain audio."
            )

        if self.audio_file_duration_s < 1:

            raise custom_error(
                ValueError,
                dev_message="Duration must be more than 1s.",
                user_message="Duration must be more than 1s."
            )

        return True


    def _replace_original_audio_file_bytes_with_normalised_version(self, normalised_bytes:bytes):

        #in views.py, InMemoryUploadedFile and TemporaryUploadedFile can be written into
        #if you have issues with writing, e.g. during tests, check your mode arg in io.BytesIO(path, mode="rb+")

        #delete existing bytes
        self.audio_file.truncate(0)

        self.audio_file.seek(0)

        #write in
        #good practice to use chunks(), even when unnecessary for memory, as per docs
        for chunk in ContentFile(normalised_bytes).chunks():

            self.audio_file.write(chunk)

        self.audio_file.seek(0)


    def get_peaks_by_buckets(self) -> list[float]:

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

        self.audio_file.seek(0)

        #get peaks
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-f', 'lavfi',
                '-i', ffprobe_i,
                '-show_entries', 'frame_tags=lavfi.astats.Overall.Peak_level',
                '-of', 'json'
            ],
            input=self.audio_file.read(),
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file.seek(0)

        result = json.loads(result.stdout)

        #extract peaks
        peak_buckets = []

        for count in range(self.bucket_quantity):

            #we fill the bucket to full first, then use last stored bucket to evaluate extra buckets
            peak_to_store = 0

            #value is in dBFS, max 0, min is approx. 6dB per bit depth
            #so bigger negative value means more quiet
            peak_to_store = float(result['frames'][count]['tags']['lavfi.astats.Overall.Peak_level'])

            #prevent exceeding floor
            if peak_to_store < self.dbfs_floor:

                peak_to_store = self.dbfs_floor

            #should never have > 0dB (will produce audio clipping), mainly because we'll normalise to prevent it
            if peak_to_store > 0:
                
                raise custom_error(
                    ValueError,
                    dev_message="Peak is over 0dBFS, which will clip. Calculating peaks process has been halted.",
                    user_message="Audio normalisation had failed, as there were above 0dBFS peaks detected."
                )

            #get percentage
            # -x / -y will always be positive
            peak_to_store = peak_to_store / self.dbfs_floor

            #invert percentage
            peak_to_store = 1 - peak_to_store

            #get 0 to 1 value
            peak_to_store = peak_to_store * 1

            #truncate
            peak_to_store = float(round(peak_to_store, 2))

            #while peak_buckets is not yet full, fill until full
            if count < self.bucket_quantity:

                peak_buckets.append(peak_to_store)
                continue

            #handle extra buckets
            #store the higher peak between last stored peak and current peak
            if peak_buckets[self.bucket_quantity] < peak_to_store:

                peak_buckets[self.bucket_quantity] = peak_to_store

        self.peak_buckets = peak_buckets
        return peak_buckets


    def do_normalisation(self) -> bytes:

        #"loudnorm=I=-16:TP=-1.5:LRA=11" is from loudnorm docs on EBU R 128
        #"loudnorm=I=-23:LRA=7:TP=-2" is from ffmpeg-normalize on EU's LUFS -23 regulation
        loudnorm_args = "loudnorm=I=-23:TP=-2:LRA=7"

        #I is LUFS
        #LRA is loudness range, i.e. range between softest and loudest parts
        #TP is true peak, -2 seems common, just be sure to give enough headroom towards 0, and never over 0

        self.audio_file.seek(0)

        #first pass, get measurement
        ffmpeg_cmd = subprocess.run(
            [
                "ffmpeg",
                "-i", "pipe:0",
                "-af", loudnorm_args + ":print_format=json",
                '-f', "null", "/dev/null"
            ],
            input=self.audio_file.read(),
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file.seek(0)

        #get print string from stderr
        first_pass_data = ffmpeg_cmd.stderr.decode()

        #construct our json string
        #this will work as long as entire print string only has one {}
        first_pass_dict = re.search(r"(\{[\s\S]*\})", first_pass_data)[0]

        if first_pass_dict is None:

            raise custom_error(
                ValueError,
                dev_message="Regex could not find the data needed for first_pass_dict via regex.",
                user_message=""
            )

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
                "ffmpeg",
                "-i", "pipe:0",
                "-af", ffmpeg_cmd_af,
                "-ar", self.desired_sample_rate,           #sample rate; mp3 can only choose 32000/44100/48000
                # "-b:a", "124k",         #bit rate, not sure if safe/redundant/necessary
                "-c:a", self.desired_codec,          #codec; a is audio, v is video
                "-f", self.desired_format, "pipe:1"   #f is format; for disk files, can just write "my_folder/file.mp3"
            ],
            input=self.audio_file.read(),
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file.seek(0)

        output = ffmpeg_cmd.stdout

        self._replace_original_audio_file_bytes_with_normalised_version(output)

        return output


    def close_audio_file(self):

        #must call this when you're done with .open()
        #other types will be auto-closed by Django at end of request
        self.audio_file.close()


class CreateAudioClips:

    def __init__(
        self, user, current_context:Literal["create_event", "create_reply"],
        event_create_daily_limit:int, event_reply_daily_limit:int,
        event_reply_expiry_seconds:int,
    ):

        if current_context not in ["create_event", "create_reply"]:

            raise ValueError('Invalid context.')

        if user.is_authenticated is False:

            raise ValueError('User must be logged in.')

        self.user = user
        self.current_context:Literal["create_event", "create_reply"] = current_context
        self.event_create_daily_limit = event_create_daily_limit
        self.event_reply_daily_limit = event_reply_daily_limit
        self.event_reply_expiry_seconds = event_reply_expiry_seconds

        self.datetime_now = get_datetime_now()

        self.generic_status_incomplete = None
        self.generic_status_completed = None

        self.event_reply_queue = None


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


    def _check_user_can_create_reply(self)->tuple[bool, None|Response]:

        if self.event_reply_queue is None:

            raise custom_error(
                ValueError,
                dev_message="EventReplyQueue not yet retrieved. Call self._get_event_reply_queue()."
            )

        #deny if not yet replying
        if self.event_reply_queue.is_replying is False:

            return (
                False,
                Response(
                    data={
                        'message': "You have not selected this event to reply in.",
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            )

        #is replying, proceed

        #check that event is still ok
        if self.event_reply_queue.event.generic_status.generic_status_name != 'incomplete':

            #remove expired reply choice
            self.event_reply_queue.delete()
            self.event_reply_queue = None

            return (
                False,
                Response(
                    data={
                        'message': "This event is no longer available.",
                        'can_retry': False,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            )

        #check for expiry
        if(
            self.event_reply_queue.when_locked <
            (self.datetime_now - timedelta(seconds=self.event_reply_expiry_seconds))
        ):

            #remove expired reply choice
            self.event_reply_queue.delete()
            self.event_reply_queue = None

            return (
                False,
                Response(
                    data={
                        'message': "Reply was not successful. Time limit was reached.",
                        'can_retry': False,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            )

        return (
            True,
            None
        )


    def _create_event(self, event_name:str):

        if self.current_context != "create_event":

            raise custom_error(
                ValueError,
                dev_message="Cannot create events with current_context."
            )

        if self.generic_status_incomplete is None:

            self.generic_status_incomplete = GenericStatuses.objects.get(generic_status_name='incomplete')

        self.event = Events.objects.create(
            event_name=event_name,
            generic_status=self.generic_status_incomplete,
            created_by=self.user,
        )


    def _get_event_reply_queue(self, event_id:int):

        self.event_reply_queue = EventReplyQueues.objects.select_for_update(
            of=("self",)
        ).select_related(
            'event__generic_status'
        ).get(
            event_id=event_id,
            locked_for_user=self.user
        )


    def create_event_and_audio_clip_as_originator(self, event_name:str, audio_clip_tone_id:int, audio_file):

        if self.current_context != "create_event":

            raise custom_error(
                ValueError,
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

        #audio_file, further validation
        #on error, will raise by themselves
        handle_audio_file_class = HandleAudioFile(audio_file, True)

        #prepare audio file info, which also self-validates
        #reminder that .size check should be done at form/serializer
        handle_audio_file_class.prepare_audio_file_info()

        #normalize
        handle_audio_file_class.do_normalisation()

        #get peaks
        handle_audio_file_class.get_peaks_by_buckets()

        #if it reaches here with no problems, then audio_file is fine
        #create event
        self._create_event(event_name)

        #create audio_clip, excluding audio_file and event
        #generic_status is handled by default, so it is skipped here
        new_audio_clip = AudioClips.objects.create(
            user=self.user,
            audio_clip_role=audio_clip_role,
            audio_clip_tone=audio_clip_tone,
            event=self.event,
            audio_volume_peaks=handle_audio_file_class.peak_buckets,
            audio_duration_s=handle_audio_file_class.audio_file_duration_s
        )

        #we delay saving audio_file, as we want when_created for audio_file's path
        new_audio_clip.audio_file = handle_audio_file_class.audio_file
        new_audio_clip.save()

        #close just in case it's no longer a reference, i.e. Django won't auto-close
        handle_audio_file_class.close_audio_file()

        return Response(
            data={
                "message": "Event was successfully created!",
                "event_id": new_audio_clip.event_id,
            },
            status=status.HTTP_201_CREATED
        )


    def create_audio_clip_as_responder(self, event_id:int, audio_clip_tone_id:int, audio_file):

        if self.current_context != "create_reply":

            raise custom_error(
                ValueError,
                dev_message="Invalid current_context."
            )

        #get queue
        self._get_event_reply_queue(event_id)

        #perform checks

        can_create_reply, response = self._check_user_can_create_reply()

        if can_create_reply is False:

            return response

        #no need to check for daily reply limit here
        #as that is enforced when listing choices

        #can reply, proceed

        audio_clip_role = AudioClipRoles.objects.get(audio_clip_role_name='responder')
        audio_clip_tone = AudioClipTones.objects.get(pk=audio_clip_tone_id)

        #audio_file, further validation
        #on error, will raise by themselves
        handle_audio_file_class = HandleAudioFile(audio_file, True)

        #prepare audio file info, which also self-validates
        #reminder that .size check should be done at form/serializer
        handle_audio_file_class.prepare_audio_file_info()

        #normalize
        handle_audio_file_class.do_normalisation()

        #get peaks
        handle_audio_file_class.get_peaks_by_buckets()

        #create audio_clip, excluding audio_file and event
        #generic_status is handled by default, so it is skipped here
        new_audio_clip = AudioClips.objects.create(
            user=self.user,
            audio_clip_role=audio_clip_role,
            audio_clip_tone=audio_clip_tone,
            event_id=self.event_reply_queue.event_id,
            audio_volume_peaks=handle_audio_file_class.peak_buckets,
            audio_duration_s=handle_audio_file_class.audio_file_duration_s
        )

        #we delay saving audio_file, as we want when_created for audio_file's path
        new_audio_clip.audio_file = handle_audio_file_class.audio_file
        new_audio_clip.save()

        #close just in case it's no longer a reference, i.e. Django won't auto-close
        handle_audio_file_class.close_audio_file()


        if self.generic_status_completed is None:

            self.generic_status_completed = GenericStatuses.objects.get(generic_status_name='completed')

        #update event as completed
        Events.objects.filter(
            pk=self.event_reply_queue.event_id
        ).update(
            generic_status=self.generic_status_completed,
            last_modified=self.datetime_now
        )

        #remove event_reply_queue
        self.event_reply_queue.delete()
        self.event_reply_queue = None

        return Response(
            data={
                "message": "Reply was successfully created!",
            },
            status=status.HTTP_201_CREATED
        )

























