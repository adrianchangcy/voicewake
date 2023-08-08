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
from django.template.loader import get_template
from django.core.mail import send_mail
from django.core.files.uploadedfile import InMemoryUploadedFile

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

#app files
from .models import *

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

    return re.sub(r'\s+', '', string_value)


def has_numbers_only(string_value):

    return re.match(r'^[0-9]+$', string_value) is not None


def construct_timed_out_message(seconds:float, text_before_timeout='', text_after_timeout=''):

        timeout_pretty_minutes = seconds / 60
        timeout_pretty_seconds = seconds % 60

        if timeout_pretty_minutes > 0 and timeout_pretty_seconds > 0:

            return '''
                %s%s minutes and %s seconds%s
                ''' % (
                    text_before_timeout,
                    str(timeout_pretty_minutes),
                    str(timeout_pretty_seconds),
                    text_after_timeout
                )

        elif timeout_pretty_minutes > 0:

            return '''
                %s%s minutes%s
                ''' % (
                    text_before_timeout,
                    str(timeout_pretty_minutes),
                    text_after_timeout
                )

        elif timeout_pretty_seconds > 0:

            return '''
                %s%s seconds%s
                ''' % (
                    text_before_timeout,
                    str(timeout_pretty_seconds),
                    text_after_timeout
                )
        
        return ''


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



#inherits TOTPVerification class
#always use this class in transaction.atomic()
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
        time_remaining = (timeout_end - get_datetime_now()).total_seconds()
        time_remaining = math.ceil(time_remaining)

        return time_remaining


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
        time_remaining = (timeout_end - get_datetime_now()).total_seconds()
        time_remaining = math.ceil(time_remaining)

        return time_remaining


    def has_otp_saved(self):

        return self.user_otp_instance is not None and self.user_otp_instance.otp != ''


    def generate_and_save_otp(self):

        self._set_key_if_none()

        if self.is_creating_otp_timed_out() is True:

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


    def get_default_verify_otp_response():

        #always return this Response when error to give 0 clues on whether user exists or not
        return Response(
            data={
                'message': 'Your code did not match the latest one that we sent.',
                'verify_otp_success': False
            },
            status=status.HTTP_400_BAD_REQUEST
        )


    def get_default_create_otp_response(email):

        #always return this Response when error to give 0 clues on whether user exists or not
        return Response(
            data={
                'message': 'Verification code has been sent to %s.' % (email),
            },
            status=status.HTTP_200_OK
        )


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

    def __init__(self):

        #max timeout seconds for subprocess
        self.subprocess_timeout_s = 10

        self.audio_file_info = None

        #dBFS has max 0dB (loudest), min of approx. 6dB per bit, e.g. 16-bit will have 96dB floor
        # >0 will cause clipping
        #since we need 0 to 1 to draw peaks at frontend, but we don't know our floor (lack of bit depth info),
        #we assume via ffmpeg's silencedetect of default -60dB
        self.dbfs_floor = -60


    def get_audio_file_info(self, audio_file:Union[InMemoryUploadedFile, str])->dict:

        if type(audio_file) == InMemoryUploadedFile:

            audio_file.seek(0)

            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-show_streams',
                    '-of', 'json',
                    '-i', 'pipe:0'
                ],
                stdin=audio_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=self.subprocess_timeout_s
            )

            audio_file.seek(0)

        else:

            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-show_streams',
                    '-of', 'json',
                    '-i', audio_file
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=self.subprocess_timeout_s
            )

        self.audio_file_info = json.loads(result.stdout)
        return self.audio_file_info


    def get_peaks_by_buckets(self, audio_file:Union[InMemoryUploadedFile, str], bucket_quantity:int=20) -> list[float]:

        #get duration
        #get sample rate
        #asetnsamples = (duration / x buckets) * sample rate
        #expect x + 1 buckets output, so compare second last and last bucket and select the one with higher peak

        #get necessary info
        sample_rate = int(self.audio_file_info['streams'][0]['sample_rate'])
        duration = float(self.audio_file_info['format']['duration'])

        #calculate appropriate sample rate to get bucket_quantity + 1
        asetnsamples = math.floor(duration / bucket_quantity * sample_rate)

        #to get highest peak per x, add "asetnsamples=x" after amovie, i.e. chunk size, e.g. "amovie=...,asetnsamples=x,..."
        #e.g. if file is 48000Hz frequency, i.e. 48000 samples/sec, asetnsamples=48000 gives you 1 sec/bucket
        final_input = 'amovie=%s,asetnsamples=%s,astats=metadata=1:reset=1' % (audio_file, str(asetnsamples))

        #if full path, format properly
        if type(audio_file) == InMemoryUploadedFile:

            audio_file.seek(0)

            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-f', 'lavfi',
                    '-i', 'pipe:0',
                    '-show_entries', 'frame_tags=lavfi.astats.Overall.Peak_level',
                    '-of', 'json'
                ],
                stdin=audio_file,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=self.subprocess_timeout_s
            )

            audio_file.seek(0)

        else:

            #target actual backslash (\) via double backslash to escape it, and replace with forward slash
            audio_file = audio_file.replace('\\', '/')
    
            #colon (:) must be escaped, as it's a valid operator
            #we need extra escaping, since shlex.split() seems to remove one layer of our escaping
            audio_file = audio_file.replace(':', '\\\\\\:')

            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-f', 'lavfi',
                    '-i', final_input,
                    '-show_entries', 'frame_tags=lavfi.astats.Overall.Peak_level',
                    '-of', 'json'
                ],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=self.subprocess_timeout_s
            )

        result = json.loads(result.stdout)

        #extract peaks
        bucket_peaks = []

        for count in range(bucket_quantity):

            peak = 0

            if count < bucket_quantity - 1:

                #proceed as usual

                #value is in dBFS, max 0, min is approx. 6dB per bit depth
                #so bigger negative value means more quiet
                peak = float(result['frames'][count]['tags']['lavfi.astats.Overall.Peak_level'])

            elif (count == bucket_quantity - 1) and (len(result['frames']) == bucket_quantity + 1):

                #we sometimes get bucket_quantity + 1
                #if so, select the higher peak between second last and last peak

                second_last_peak = float(result['frames'][count]['tags']['lavfi.astats.Overall.Peak_level'])
                last_peak = float(result['frames'][count+1]['tags']['lavfi.astats.Overall.Peak_level'])

                if second_last_peak > last_peak:
                    
                    peak = second_last_peak

                else:

                    peak = last_peak

            #prevent exceeding floor
            if peak < self.dbfs_floor:

                peak = self.dbfs_floor

            #should never have > 0dB, mainly because we'll normalise to prevent it
            #on the rare chance that there is, we should at least record it correctly
            if peak > 0:
                
                peak = 0

            #get percentage
            # -x / -y will always be positive
            peak = peak / self.dbfs_floor

            #invert percentage
            peak = 1 - peak

            #get 0 to 1 value
            peak = peak * 1

            #truncate
            peak = float(round(peak, 2))

            #store
            bucket_peaks.append(peak)

        return bucket_peaks


    def normalise_audio_file(self, audio_file:InMemoryUploadedFile) -> bytes:

        #ffmpeg-normalize is used to normalise audio to EBU R 128 loudness standard
        #default "-c:a pcm" (pcm codec) and ".mkv" container/extension, but the file size is too big
        #-o will auto-infer the preferred file extension based on the specified file path + name
        #two options:
            #"-c:a aac", "...mp4"
            #"-c:a mp3", "...mp3"

        normalization_type = "ebu" #ebu/rms/peak
        target_level = -23

        #first pass, to get required data
        output = subprocess.check_output(
            [
                "ffmpeg", "-nostdin", "-y",
                "-i", "pipe:0",
                "-af", "astats=measure_overall=Peak_level+RMS_level:measure_perchannel=0",
                "-vn", "-sn",
                "-f", "null", "/dev/null"
            ],
            stdin=audio_file,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=self.subprocess_timeout_s
        )

        #whether file is passed into subprocess or you do file.read(), you must reset via .seek(0)
        #else, second reference has zero bytes
        audio_file.seek(0)

        mean_volume_matches = re.findall(r"RMS level dB: ([\-\d\.]+)", output)
        if mean_volume_matches:
            detected_mean = float(mean_volume_matches[0])
        else:
            raise RuntimeError("Could not detect mean volume")

        max_volume_matches = re.findall(r"Peak level dB: ([\-\d\.]+)", output)
        if max_volume_matches:
            detected_max = float(max_volume_matches[0])
        else:
            raise RuntimeError("Could not detect max volume")

        if normalization_type == "ebu":
            adjustment = 0
        elif normalization_type == "peak":
            adjustment = 0 + target_level - detected_max
        elif normalization_type == "rms":
            adjustment = target_level - detected_mean

        #second pass, with required data ready
        output = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", "pipe:0",
                "-af", f"volume={adjustment}dB",
                "-vn", "-sn",
                "-f", "mp3", "pipe:1"
            ],
            stdin=audio_file,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            timeout=self.subprocess_timeout_s
        )

        audio_file.seek(0)

        #ebu: range is -70 to -5.0
        #others: range is -99 to 0
        return output

















