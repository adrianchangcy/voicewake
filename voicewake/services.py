#here, we define helpers

#Django libraries
from django.db.models import Q, Case, When, Value
from django.db import connection
from django.core.files import File
from rest_framework.response import Response
from rest_framework import status
from django_otp.oath import TOTP
from django.contrib.auth import get_user_model
from django.db import transaction

#Python libraries
from datetime import datetime, timezone, timedelta, tzinfo
from genericpath import isfile
from zoneinfo import ZoneInfo
from pydub import AudioSegment
import secrets
import time
import re
import math

#app files
from .models import *
from .serializers import *
from .settings import *

#miscellaneous
from .static.values.values import *



#call this function as REST API via a standalone script, then run that script via cronjob
#we currently rely on ffmpeg conversion to check for file integrity
def convert_event_audio_files_to_mp3():

    #find files to convert to mp3
    events = Events.objects.filter(
        Q(audio_file__isnull=False) &
        Q(event_status__event_status_name='waiting_for_mp3_conversion')
    ).order_by('when_created')[:10]
    
    if len(events) == 0:
        
        #nothing to process
        return

    old_files_to_delete = []

    for event in events:

        source = event.audio_file.path
        split_name_and_extension = source.rsplit('.', 1)
        extension = split_name_and_extension[-1]

        #queue "old" non-mp3 files for deletion
        #no need to delete "old" non-mp3 files because ffmpeg will replace for us
        if extension != 'mp3':

            old_files_to_delete.append(source)

        try:

            #make mp3 the default, as aac needs further configurations
            #new files from export() will replace themselves
            sound = AudioSegment.from_file(source, format=extension)
            new_source = split_name_and_extension[0] + '.' + 'mp3'
            sound.export(new_source, format='mp3', bitrate='192k')

            #assign new file to Events object
            with open(new_source) as f:
                
                new_name = (event.audio_file.name).rsplit('.', 1)[0] + '.' + 'mp3'
                event.audio_file = File(f, name=new_name)
                # event.event_status = EventStatuses.objects.get(event_status_name='file_ready')

                f.close()

        except:

            #handle faulty file
            event.audio_file = None
            # event.event_status = EventStatuses.objects.get(event_status_name='file_error')

            continue

    Events.objects.bulk_update(events, ['event_status', 'audio_file'])

    for old_file in old_files_to_delete:

        if os.path.isfile(old_file):

            os.remove(old_file)

    return True


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


def get_datetime_now():

    return datetime.now().astimezone(tz=ZoneInfo('UTC'))

    #to get difference
    #minutes_passed = (get_datetime_now() - event_room.when_locked).total_seconds() / 60
    #hours_passed = (get_datetime_now() - event_room.when_locked).total_seconds() / 60 / 60


def remove_all_whitespace(string_value):

    return re.sub(r'\s+', '', string_value, flags=re.UNICODE)


def has_numbers_only(string_value):

    return re.match(r'^[0-9]+$', string_value, flags=re.UNICODE) is not None


def construct_timed_out_message(seconds:float, error_description='', text_before_timeout=''):

        timeout_pretty_minutes = seconds / 60
        timeout_pretty_seconds = seconds % 60

        if timeout_pretty_minutes > 0 and timeout_pretty_seconds > 0:

            return '''
                %s %s %s minutes and %s seconds.
                ''' % (
                    error_description,
                    text_before_timeout,
                    str(timeout_pretty_minutes),
                    str(timeout_pretty_seconds)
                )

        elif timeout_pretty_minutes > 0:

            return '''
                %s %s %s minutes.
                ''' % (
                    error_description,
                    text_before_timeout,
                    str(timeout_pretty_minutes)
                )

        elif timeout_pretty_seconds > 0:

            return '''
                %s %s %s seconds.
                ''' % (
                    error_description,
                    text_before_timeout,
                    str(timeout_pretty_seconds)
                )
        
        return ''


#you do not need this if you have appropriate permission_classes=[]
def is_user_logged_in(request):

    return request.user.is_authenticated

def is_user_banned(request):

    #??
    return False

def check_user_is_replying(request, exclude_event_room_id=None):

    User = get_user_model()

    #check if user is replying to anything
    if exclude_event_room_id is None:

        the_count = EventRooms.objects.filter(
            locked_for_user=User(pk=request.user.id),
            is_replying=True
        ).count()

    else:

        the_count = EventRooms.objects.filter(
            locked_for_user=User(pk=request.user.id),
            is_replying=True
        ).exclude(
            pk=exclude_event_room_id
        ).count()

    return the_count > 0

def prevent_event_room_from_queuing_twice_for_reply(user, event_room):

    user_event_room, ok = UserEventRooms.objects.get_or_create(
        user=user,
        event_room=event_room,
    )

    user_event_room.is_excluded_for_reply = True
    user_event_room.save()



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



#utilise this class in transaction.atomic()
class HandleUserOTP(TOTPVerification):

    def __init__(
        self, user_instance,
        totp_number_of_digits, totp_validity_seconds, totp_tolerance_seconds,
        otp_create_timeout_seconds, otp_max_attempts, otp_max_attempt_timeout_seconds
    ):

        self.user_instance = user_instance
        self.user_otp_instance = None

        self.otp_create_timeout_seconds = otp_create_timeout_seconds
        self.otp_max_attempts = otp_max_attempts
        self.otp_max_attempt_timeout_seconds = otp_max_attempt_timeout_seconds

        TOTPVerification.__init__(self, totp_number_of_digits, totp_validity_seconds, totp_tolerance_seconds)


    def _set_key_if_none(self):

        if self.key is None:

            self.key = bytes(self.user_instance.totp_key)


    def get_or_create_user_otp_instance(self):

        if self.user_otp_instance is None:

            self.user_otp_instance, created = UserOTP.objects.select_for_update().get_or_create(user=self.user_instance)


    def get_user_instance(self):

        return self.user_instance


    def get_user_otp_instance(self):

        return self.user_otp_instance
    

    def reset_user_otp_instance(self):

        if self.user_otp_instance is not None:

            self.user_otp_instance.attempts = 0
            self.user_otp_instance.otp = ''
            self.user_otp_instance.save()


    def is_max_attempts_timed_out(self):

        #max attempts reached
        if self.user_otp_instance.attempts >= self.otp_max_attempts:

            #check for timeout
            timeout_end = self.user_otp_instance.last_attempted + timedelta(seconds=self.otp_max_attempt_timeout_seconds)

            if get_datetime_now() < timeout_end:

                #still under timeout
                print('Is timed out from max attempts.')
                return True

            #reset after timeout
            self.reset_user_otp_instance()
            return False
        
        return False


    def get_max_attempts_timed_out_seconds_left(self):

        if self.is_max_attempts_timed_out() is False:

            return 0
        
        timeout_end = self.user_otp_instance.last_attempted + timedelta(seconds=self.otp_max_attempt_timeout_seconds)

        return (timeout_end - get_datetime_now()).total_seconds()


    def is_creating_otp_timed_out(self):

        #check for timeout
        timeout_end = self.user_otp_instance.when_created + timedelta(seconds=self.otp_create_timeout_seconds)

        #UserOTP will first be created with otp == ''
        if get_datetime_now() < timeout_end and len(self.user_otp_instance.otp) > 0:

            print('Is timed out from creating OTP.')
            return True
        
        return False


    def get_creating_otp_timed_out_seconds_left(self):

        if self.is_creating_otp_timed_out() is False:

            return 0
        
        timeout_end = self.user_otp_instance.when_created + timedelta(seconds=self.otp_create_timeout_seconds)

        return (timeout_end - get_datetime_now()).total_seconds()


    def has_otp_saved(self):

        return self.user_otp_instance.otp != ''


    def generate_and_save_otp(self):

        self._set_key_if_none()

        if self.is_creating_otp_timed_out() is True or self.is_max_attempts_timed_out() is True:

            return ''

        #having an existing OTP already saved does not matter, just replace
        self.user_otp_instance.otp = self.generate_token()
        self.user_otp_instance.when_created = get_datetime_now()
        self.user_otp_instance.save()
        return self.user_otp_instance.otp


    def verify_otp(self, otp:str):

        self._set_key_if_none()

        #reminder that is_max_attempts_timed_out() calls reset_user_otp_instance() appropriately for us
        if self.is_max_attempts_timed_out() is True or self.has_otp_saved() is False:

            return False
        
        #record attempt
        self.user_otp_instance.attempts += 1
        self.user_otp_instance.last_attempted = get_datetime_now()

        #check token validity
        if otp != self.user_otp_instance.otp or self.verify_token(otp) is False:

            self.user_otp_instance.save()
            return False
        
        #ok
        self.user_otp_instance.delete()
        self.user_otp_instance = None
        return True


    def get_default_error_response(self):

        #always return this Response when error to give 0 clues on whether user exists or not
        return Response(
            data={
                'message': 'Your verification code did not match the latest one that was sent.',
            },
            status=status.HTTP_200_OK
        )







