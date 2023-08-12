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
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.core.files.base import ContentFile

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

    def __init__(self, audio_file:Union[InMemoryUploadedFile, TemporaryUploadedFile], overwrite_source:bool):

        #we do not accept abs path, because our code overrides the passed file to save memory
        #i.e. InMemoryUploadedFile/TemporaryUploadedFile makes .save() go smoothly
        #preventing override would mean duplicating memory/disk space, and ensuring disk copy is deleted
        if overwrite_source is False:

            raise ValueError("Current code will always overwrite original source's bytes to save memory.")

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
        self.dbfs_floor = -60

        self.bucket_quantity = 20

        #check type
        if type(audio_file) not in [InMemoryUploadedFile, TemporaryUploadedFile]:

            raise TypeError('audio_file must be of type [str, InMemoryUploadedFile, TemporaryUploadedFile].')
        
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

            raise TypeError("Cannot validate audio_file_info when it is None.")
        
        #audio_file_info['streams'] can have multiple dicts if there's not only audio in it
        #e.g. a flac file from an album for test has a jpeg in it with ['index'] == 1
        #don't know whether the index order is always fixed, hence the loop

        for count, stream in enumerate(self.audio_file_info['streams']):

            if stream['codec_name'] in ["opus", "mp3"]:

                break

            elif count == len(self.audio_file_info['streams']) - 1:

                raise RuntimeError("Codec is not opus/mp3.")
        
        if self.audio_file_duration_s < 1:

            raise ValueError("Duration must be more than 1s.")
        
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
                
                raise ValueError('Peak is over 0dBFS, which will clip. Calculating peaks process has been halted.')

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
        #we do TP=-2 instead, to feel better about supposedly "more than enough headroom"
        #Spotify does -2 too

        self.audio_file.seek(0)

        #first pass, get measurement
        ffmpeg_cmd = subprocess.run(
            [
                "ffmpeg",
                "-i", "pipe:0",
                "-af", "loudnorm=I=-16:TP=-2:LRA=11:print_format=json",
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

            raise ValueError("Regex could not find first pass dict.")
        
        #transform into proper dict
        first_pass_dict = json.loads(first_pass_dict)
        first_pass_dict = dict(first_pass_dict)

        #prepare -af values for second pass
        #can't directly .format() here, must call the variable again
        ffmpeg_cmd_af = "loudnorm=I=-16:TP=-2:LRA=11" +\
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

        if len(output) == 0:

            raise MemoryError("Empty bytes returned when normalising. Maybe you've forgotten to do .seek(0)?")

        self._replace_original_audio_file_bytes_with_normalised_version(output)

        return output


    def close_audio_file(self):

        #must call this when you're done with .open()
        #other types will be auto-closed by Django at end of request
        self.audio_file.close()

















