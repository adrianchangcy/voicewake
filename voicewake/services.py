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

    def __init__(self, number_of_digits, validity_seconds, tolerance_seconds):

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
        self.number_of_digits = number_of_digits

        # validity period of a token. Default is 30 seconds.
        self.token_validity_period = validity_seconds

        self.token_validity_tolerance = tolerance_seconds

    def totp_obj(self):

        # create a TOTP object
        totp = TOTP(
            key=self.key,
            step=self.token_validity_period,
            digits=self.number_of_digits
        )

        # the current time will be used to generate a counter
        totp.time = time.time()

        return totp
    
    def set_key(self, key):

        self.key = key

    def create_key(self, key_byte_size):

        self.key = secrets.token_bytes(key_byte_size)

    def get_key(self):

        return self.key

    def generate_token(self):

        # get the TOTP object and use that to create token
        totp = self.totp_obj()

        # token can be obtained with `totp.token()`
        token = str(totp.token())
        token = token.zfill(self.number_of_digits)
        return token

    def verify_token(self, token):

        try:

            # convert the input token to integer
            token = int(token)

        except ValueError:

            # return False, if token could not be converted to an integer
            self.verified = False

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

class HandleUserOTP:

    def __init__(self, user_instance):

        #User row
        self.user_instance = user_instance





#True when updated, False when still under timeout
#pass is_reset=True to reset, when user's submitted OTP is verified successfully
def increment_user_otp_attempt(hard_reset=False):

    user_instance = get_user_model()(pk=1)
    datetime_now = get_datetime_now()

    try:

        with transaction.atomic():

            user_otp_instance = UserOTP.objects.select_for_update().get(
                user=user_instance
            )

            #hard reset on OTP success
            if hard_reset is True:

                user_otp_instance.attempts = -1
                user_otp_instance.save()
                return True

            #max attempts reached
            if user_otp_instance.attempts >= TOTP_MAX_ATTEMPTS:

                #check for timeout
                timeout_end = user_otp_instance.last_attempted + timedelta(seconds=TOTP_MAX_ATTEMPT_TIMEOUT_SECONDS)

                if datetime_now < timeout_end:

                    #still under timeout
                    return False

                else:

                    #can reset after timeout
                    user_otp_instance.attempts = -1
                    user_otp_instance.save()
                    return True

            #proceed
            user_otp_instance.attempts += 1
            user_otp_instance.save()
            return True

    except:

        return False





