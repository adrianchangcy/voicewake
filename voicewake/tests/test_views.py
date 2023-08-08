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
from django.core.files.uploadedfile import InMemoryUploadedFile

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


    def test_file_handling_from_request(self):

        # audio_file = 'events/year_2023/month_7/day_21/user_id_1/e_13.webm'
        # process_audio_file_class = HandleAudioFile(audio_file)

        #example file
        audio_file_full_path = os.path.join(settings.MEDIA_ROOT, 'events/year_2023/month_7/day_21/user_id_1/e_13.webm')

        #simulate InMemoryUploadedFile
        audio_file = InMemoryUploadedFile(
            io.FileIO(audio_file_full_path),
            'FileField',                            #to-be field if it were in form/serializer
            'new_recording.webm',                   #doesn't have to match actual file name
            'audio/webm',                           #Content-Type
            os.path.getsize(audio_file_full_path),  #use os.path.getsize(path) for file size, not sys.getsizeof()
            None
        )


        #first pass, get measurement
        ffmpeg_cmd = subprocess.run(
            [
                "ffmpeg",
                "-i", "pipe:0",
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                '-f', "null", "/dev/null"
            ],
            stdin=audio_file,
            check=True,
            capture_output=True,
            timeout=10
        )

        audio_file.seek(0)

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
        #can't directly .format(), must call the variable again
        ffmpeg_cmd_af = "loudnorm=I=-16:TP=-1.5:LRA=11" +\
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
                "-ar", "48k",           #sampling rate
                "-c:a", "mp3",          #codec, a is audio, v is video
                "-f", "mp3", "pipe:1"   #f is format; for disk files, can just write "my_folder/file.mp3"
            ],
            stdin=audio_file,
            stdout=subprocess.PIPE,
            timeout=10
        )

        print(type(ffmpeg_cmd.stdout))

        return

        #validate audio size, info, extension
        #once basic validation is done, save file to disk
        from tempfile import NamedTemporaryFile

        #simulate TemporaryUploadedFile
        temp_audio_file = NamedTemporaryFile(
            dir=settings.MEDIA_ROOT,
            suffix=".webm",
            delete=False
        )

        #simulate transferring InMemoryUploadedFile to TemporaryUploadedFile
        #must do it this way to overcome Window's permission denied issue
        with temp_audio_file as my_file:

            #write from memory to tmp file on disk
            my_file.write(audio_file.read())
            my_file.seek(0)

            print(my_file.name)

            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-i', my_file.name,
                    '-show_entries', 'format=duration',
                    '-show_streams',
                    '-of', 'json',
                ],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=10
            )

            print(result.stdout)

            #close before deleting
            my_file.close()

            #manually delete
            os.unlink(my_file.name)





























