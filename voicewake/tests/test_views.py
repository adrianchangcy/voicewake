#this is where you write unit testing as per Django's ways
#proper ways coming soon
#Django
from time import sleep
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from django.core.files import File
from django.http import StreamingHttpResponse
from django.contrib.auth import get_user_model
from django.core import mail

#apps
from voicewake.services import *
from voicewake.models import *
from django.conf import settings

#py packages
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import os
import shutil
import math


def ensure_otp_is_always_wrong(otp):

    if int(otp[0]) == 0:
        otp = '1' + otp[1:]
    else:
        otp = str(int(otp[0]) - 1) + otp[1:]

    return otp



class Users_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.email = 'user1@gmail.com'
        cls.expected_mail_outbox_count = 0


    def test_sign_up_correctly(self, another_email=''):

        if len(another_email) > 0:

            email = another_email

        else:

            email = self.email

        #create and request OTP at the same time
        response = self.client.post(reverse('users_sign_up'), data={
            'email': email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.expected_mail_outbox_count += 1
        self.assertEqual(len(mail.outbox), self.expected_mail_outbox_count)

        user_instance = get_user_model().objects.get(
            email_lowercase=email.lower()
        )

        #get OTP
        new_otp = UserOTP.objects.get(user=user_instance).otp

        #create and log in
        response = self.client.post(reverse('users_sign_up'), data={
            'email': email,
            'otp': new_otp
        })

        print(response.status_code)
        print(response.data)

        #expect
        self.assertTrue(response.data['is_logged_in'])
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        user_instance = get_user_model().objects.get(
            email_lowercase=email.lower()
        )
        self.assertTrue(user_instance.is_active)
        self.assertIsNotNone(user_instance.last_login)
        self.assertFalse(UserOTP.objects.filter(user=user_instance).exists())


    def test_sign_up_log_out(self):

        self.test_sign_up_correctly()

        response = self.client.post(reverse('users_log_out'))

        #expect
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)


    def test_log_in_for_account_that_does_not_exist(self):

        #create and request OTP at the same time
        response = self.client.post(reverse('users_log_in'), data={
            'email': self.email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.assertEqual(len(mail.outbox), 0)

        user_exists = get_user_model().objects.filter(
            email_lowercase=self.email.lower()
        ).exists()

        #user should not be created
        self.assertFalse(user_exists)

        print(response.status_code)
        print(response.data)


    def test_log_in_correctly(self):

        self.test_sign_up_correctly()

        #generate OTP
        response = self.client.post(reverse('users_log_in'), data={
            'email': self.email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.expected_mail_outbox_count += 1
        self.assertEqual(len(mail.outbox), self.expected_mail_outbox_count)

        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #get correct OTP
        #should exist even after logging in from creating account,
        #because HandleUserOTP.verify_otp() deletes UserOTP row on success
        new_otp = UserOTP.objects.get(user=user_instance).otp

        #log in
        response = self.client.post(reverse('users_log_in'), data={
            'email': self.email,
            'otp': new_otp
        })

        print(response.status_code)
        print(response.data)

        #expect
        self.assertEqual(response.wsgi_request.user.is_authenticated, True)
        self.assertTrue(response.data['is_logged_in'])
        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )
        self.assertTrue(user_instance.is_active)
        self.assertIsNotNone(user_instance.last_login)
        self.assertFalse(UserOTP.objects.filter(user=user_instance).exists())


    def test_log_in_log_out(self):

        #https://stackoverflow.com/a/32330839

        self.test_log_in_correctly()

        #log out
        response = self.client.post(reverse('users_log_out'))

        #expect
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)


    def test_set_username_not_logged_in(self):

        self.test_log_in_log_out()

        #set username
        response = self.client.post(reverse('users_set_username'), data={
            'username': 'user1',
        })

        #expect
        self.assertEqual(response.status_code, 403)


    def test_set_bad_username_is_logged_in(self):

        self.test_log_in_correctly()

        #set username
        response = self.client.post(reverse('users_set_username'), data={
            'username': 'admin',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #expect
        self.assertEqual(response.status_code, 400)
        self.assertEqual(user_instance.username, None)
        self.assertEqual(user_instance.username_lowercase, None)

        pass


    def test_set_username_is_logged_in(self):

        self.test_log_in_correctly()

        #set username
        response = self.client.post(reverse('users_set_username'), data={
            'username': 'user1',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #expect
        self.assertEqual(user_instance.username, 'user1')
        self.assertEqual(user_instance.username_lowercase, 'user1')


    def test_set_username_when_username_exists(self):

        self.test_set_username_is_logged_in()

        response = self.client.post(reverse('users_log_out'))
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)

        #new account
        another_email = 'user2@gmail.com'

        self.test_sign_up_correctly(another_email)

        #set username identical to user1
        response = self.client.post(reverse('users_set_username'), data={
            'username': 'user1',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=another_email.lower()
        )

        #expect
        self.assertEqual(user_instance.username, None)
        self.assertEqual(user_instance.username_lowercase, None)


        #set username identical to user1, but check via case insensitive
        response = self.client.post(reverse('users_set_username'), data={
            'username': 'uSEr1',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=another_email.lower()
        )

        #expect
        self.assertEqual(user_instance.username, None)
        self.assertEqual(user_instance.username_lowercase, None)

        #set username, but correct
        response = self.client.post(reverse('users_set_username'), data={
            'username': 'user2',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=another_email.lower()
        )

        #expect
        self.assertEqual(user_instance.username, 'user2')
        self.assertEqual(user_instance.username_lowercase, 'user2')



class EventTones_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        pass


    def test_initial_db_setup(self):

        with open(os.path.join(settings.BASE_DIR, 'voicewake/static/json/data_emojis_shorter.json'), encoding="utf8") as file:

            emojis = json.load(file)
            emojis = emojis.items()

            #store for bulk_create
            new_rows = []

            for row in emojis:

                (key, symbol) = row

                new_rows.append(
                    EventTones(
                        event_tone_slug=key,
                        event_tone_name=key.replace("_"," "),
                        event_tone_symbol=symbol
                    )
                )

            #bulk_create
            EventTones.objects.bulk_create(
                new_rows
            )


class Events_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        pass


    def test_get_file_duration(self):

        the_blob = 'C:\\Users\\User\\Desktop\\voicewake_py\\uploads/events/year_2023/month_7/day_21/user_id_1/e_13.webm'

        import subprocess
        import shlex

        #duration
        def get_length(input_video):
            result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', input_video], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            return float(result.stdout)
        
        #volumes
        #this works
        def get_peaks():

            the_blob = 'C\\\\\\:/Users/User/Desktop/voicewake_py/uploads/events/year_2023/month_7/day_21/user_id_1/e_13.webm'

            #to get highest peak per x, add "asetnsamples=x" after amovie, like "amovie=...,asetnsamples=x,..."
            #will divide x samples (48000Hz is 48000 samples/sec) to 1 bucket, of which you'll get the highest peak per bucket
            #e.g. if file is 48000Hz frequency, i.e. 48000 samples/sec, asetnsamples=48000 gives you 1 sec/bucket
            cmd = shlex.split('ffprobe -v error -f lavfi -i "amovie='+the_blob+',asetnsamples=48000,astats=metadata=1:reset=1" -show_entries frame_tags=lavfi.astats.Overall.Peak_level -of csv=p=0')

            #timeout by seconds, just in case
            return subprocess.run(cmd, timeout=20)
        
        def test_formatting():

            the_blob = os.path.join(settings.MEDIA_ROOT, 'events/year_2023/month_7/day_21/user_id_1/e_13.webm')

            #target actual backslash (\) via double backslash to escape it, and replace with forward slash
            the_blob = the_blob.replace('\\', '/')

            #colon (:) must be escaped, as it's a valid operator
            #we need extra escaping, since shlex.split() seems to remove one layer of our escaping
            the_blob = the_blob.replace(':', '\\\\\\:')

            #split every command into array elements
            #there's a warning that shlex is only designed for Unix shells
            #it doesn't matter, as long as it works, since there are no better solutions
            cmd = shlex.split('ffprobe -v error -f lavfi -i "amovie='+the_blob+',asetnsamples=48000,astats=metadata=1:reset=1" -show_entries frame_tags=lavfi.astats.Overall.Peak_level -of csv=p=0')

            #run
            return subprocess.run(cmd, timeout=20)
        
        class ProcessAudioFile:

            def __init__(self, audio_file:str):

                #from audio_file field, e.g.: events/year_2023/...
                self.subprocess_timeout_s = 10
                self.audio_file = audio_file
                self.audio_file_full_path = os.path.join(settings.MEDIA_ROOT, audio_file)

            
            def prepare_extra_info(self):

                result = subprocess.run(
                    [
                        'ffprobe',
                        '-v', 'error',
                        '-show_entries', 'format=duration',
                        '-show_streams',
                        '-of', 'default=noprint_wrappers=1:nokey=1',
                        self.audio_file_full_path
                    ],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    timeout=self.subprocess_timeout_s
                )
                return (result.stdout)
            

            def get_peaks_by_buckets(self, bucket_quantity:int=20) -> list[float]:

                #get duration
                #get sample rate
                #asetnsamples = (duration / x buckets) * sample rate
                #you should have x + 1 buckets, so compare second last and last bucket and select the one with higher peak

                #target actual backslash (\) via double backslash to escape it, and replace with forward slash
                audio_file = self.audio_file_full_path.replace('\\', '/')

                #colon (:) must be escaped, as it's a valid operator
                #we need extra escaping, since shlex.split() seems to remove one layer of our escaping
                audio_file = audio_file.replace(':', '\\\\\\:')

                #to get highest peak per x, add "asetnsamples=x" after amovie, like "amovie=...,asetnsamples=x,..."
                #will divide x samples (48000Hz is 48000 samples/sec) to 1 bucket, of which you'll get the highest peak per bucket
                #e.g. if file is 48000Hz frequency, i.e. 48000 samples/sec, asetnsamples=48000 gives you 1 sec/bucket
                cmd = shlex.split('ffprobe -v error -f lavfi -i "amovie='+audio_file+',asetnsamples=48000,astats=metadata=1:reset=1" -show_entries frame_tags=lavfi.astats.Overall.Peak_level -of csv=p=0')

                result = subprocess.run(cmd,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    timeout=self.subprocess_timeout_s
                )

                return result.stdout


        #format absolute path correctly
        #get duration
        #get sample rate
        #normalise (do later)
        #asetnsamples = (duration / x buckets) * sample rate
        #you should have x + 1 buckets, so compare second last and last bucket and select the one with higher peak

        audio_file = 'events/year_2023/month_7/day_21/user_id_1/e_13.webm'

        process_audio_file_class = ProcessAudioFile(audio_file)
        print(process_audio_file_class.prepare_extra_info())

















