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
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

#apps
from voicewake.services import *
from voicewake.models import *
from django.conf import settings

#py packages
import io
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import os
import shutil
import math
import subprocess
import traceback


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
        print(response.cookies)

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



class Events_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        pass

    
    def test_prepare_test_data(self):

        prepare_test_data_class = PrepareTestData(for_test=True)

        prepare_test_data_class.do_quick_start(1)


    def test_file_handling_from_request(self):

        #should have webm/opus and mp4/__ files for test, but too lazy for now
        #webm/opus works
        #https://dirask.com/posts/JavaScript-supported-Audio-Video-MIME-Types-by-MediaRecorder-Chrome-and-Firefox-jERn81

        # audio_file = 'events/year_2023/month_7/day_21/user_id_1/e_13.webm'
        # process_audio_file_class = HandleAudioFile(audio_file)

        #example file
        audio_file_full_path = os.path.join(settings.BASE_DIR, 'voicewake/tests/audio_can_overwrite.mp3')

        #automate args
        file_extension = audio_file_full_path.split(".", -1)[-1]
        temporary_audio_file_name = 'new_recording' + '.' + file_extension
        content_type = 'audio/' + file_extension

        #simulate InMemoryUploadedFile
        #if this works, then TemporaryUploadedFile() when live works too
        #since both are the same, with only 1 extra method as difference
        #can't seem to create TemporaryUploadedFile() when testing, as .read() returns b''
        audio_file_in_memory = InMemoryUploadedFile(
            io.FileIO(audio_file_full_path, mode="rb+"),
            'FileField',                            #to-be field if it were in form/serializer
            temporary_audio_file_name,              #doesn't have to match actual file name
            content_type,                           #Content-Type
            os.path.getsize(audio_file_full_path),  #use os.path.getsize(path) for file size, not sys.getsizeof()
            None
        )

        #check size, not included in HandleAudioFile
        self.assertLessEqual(audio_file_in_memory.size, settings.EVENT_MAX_FILE_SIZE_BYTES)

        #proceed
        handle_audio_file_class = HandleAudioFile(audio_file_in_memory, True)

        #process info, will raise error during validation
        self.assertEqual(handle_audio_file_class.prepare_audio_file_info(), True)

        #process peaks
        self.assertEqual(type(handle_audio_file_class.get_peaks_by_buckets()), list)

        #check
        self.assertEqual(type(handle_audio_file_class.peak_buckets), list)
        self.assertEqual(len(handle_audio_file_class.peak_buckets), handle_audio_file_class.bucket_quantity)

        for row in handle_audio_file_class.peak_buckets:
            self.assertEqual(type(row), float)

        #normalise
        self.assertEqual(type(handle_audio_file_class.do_normalisation()), bytes)

        #check
        self.assertGreater(len(handle_audio_file_class.audio_file.read()), 0)
        handle_audio_file_class.audio_file.seek(0)

        handle_audio_file_class.close_audio_file()


    def test_custom_functions(self):

        #pass in event_tone_slug
        #fetches the row if exists, else fetches all rows
        yolo = Events.objects.raw("SELECT * FROM get_id_of_one_or_all_event_tones_via_slug(%s)", params=('',))

        #check
        print(len(yolo))
        self.assertGreater(len(yolo), 0)



class RandomTests_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        pass
















































