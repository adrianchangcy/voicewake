#this is where you write unit testing as per Django's ways
#proper ways coming soon
#Django
from time import sleep
from django.test import TestCase, Client, TransactionTestCase, override_settings
from django.urls import reverse
from rest_framework import status
from django.core.files import File
from django.http import StreamingHttpResponse
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.db.models import Count
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection

#apps
from voicewake.services import *
from voicewake.models import *
from voicewake.tasks import *
from voicewake.factories import *
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
import inspect, sys
import dotenv



#tests always auto-override DEBUG to False
#manually specify it as True via @override_settings as needed



def ensure_otp_is_always_wrong(otp):

    if int(otp[0]) == 0:
        otp = '1' + otp[1:]
    else:
        otp = str(int(otp[0]) - 1) + otp[1:]

    return otp



@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'voicewake/tests'),
)
class Random_TestCase(TestCase):

    def test_random(self):

        print(settings.DEBUG)



class Users_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.email = 'user1@gmail.com'
        cls.unused_email = 'abc0123456789@gmail.com'
        cls.expected_mail_outbox_count = 0


    def test_sign_up_but_missing_otp(self):

        #generate OTP
        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.expected_mail_outbox_count += 1
        self.assertEqual(len(mail.outbox), self.expected_mail_outbox_count)

        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #sign up, with recorded email
        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.email,
        })

        self.assertTrue(response.status_code, 400)

        #sign up, with unrecorded email
        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.unused_email,
        })

        self.assertTrue(response.status_code, 400)

        #expect
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)


    def test_sign_up_correctly(self, another_email=''):

        if len(another_email) > 0:

            email = another_email

        else:

            email = self.email

        #create and request OTP at the same time
        response = self.client.post(reverse('users_sign_up_api'), data={
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
        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
            0, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )
        handle_user_otp_class.guarantee_user_otp_instance()
        new_otp = handle_user_otp_class.generate_otp()

        #create and log in
        response = self.client.post(reverse('users_sign_up_api'), data={
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

        response = self.client.post(reverse('users_log_out_api'))

        #expect
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)


    def test_log_in_for_account_that_does_not_exist(self):

        #create and request OTP at the same time
        response = self.client.post(reverse('users_log_in_api'), data={
            'email': self.email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.assertEqual(len(mail.outbox), 1)

        user_exists = get_user_model().objects.filter(
            email_lowercase=self.email.lower()
        ).exists()

        #user should be created with only email
        self.assertTrue(user_exists)

        print(response.status_code)
        print(response.data)


    def test_log_in_but_missing_otp(self):

        self.test_sign_up_log_out()

        #generate OTP
        response = self.client.post(reverse('users_log_in_api'), data={
            'email': self.email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.expected_mail_outbox_count += 1
        self.assertEqual(len(mail.outbox), self.expected_mail_outbox_count)

        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #log in with account that exists
        response = self.client.post(reverse('users_log_in_api'), data={
            'email': self.email,
        })

        self.assertTrue(response.status_code, 400)

        #log in with account that doesn't exist
        response = self.client.post(reverse('users_log_in_api'), data={
            'email': self.unused_email,
        })

        self.assertTrue(response.status_code, 400)

        #expect
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)


    def test_log_in_correctly(self):

        self.test_sign_up_log_out()

        #generate OTP
        response = self.client.post(reverse('users_log_in_api'), data={
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
        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
            0, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )
        handle_user_otp_class.guarantee_user_otp_instance()
        new_otp = handle_user_otp_class.generate_otp()

        #log in
        response = self.client.post(reverse('users_log_in_api'), data={
            'email': self.email,
            'otp': new_otp
        })

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
        response = self.client.post(reverse('users_log_out_api'))

        #expect
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)


    def test_set_username_not_logged_in(self):

        self.test_log_in_log_out()

        #set username
        response = self.client.post(reverse('users_set_username_api'), data={
            'username': 'user1',
        })

        #expect
        self.assertEqual(response.status_code, 403)


    def test_set_bad_username_is_logged_in(self):

        self.test_log_in_correctly()

        #set username
        response = self.client.post(reverse('users_set_username_api'), data={
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
        response = self.client.post(reverse('users_set_username_api'), data={
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

        response = self.client.post(reverse('users_log_out_api'))
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)

        #new account
        another_email = 'user2@gmail.com'

        self.test_sign_up_correctly(another_email)

        #set username identical to user1
        response = self.client.post(reverse('users_set_username_api'), data={
            'username': 'user1',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=another_email.lower()
        )

        #expect
        self.assertEqual(user_instance.username, None)
        self.assertEqual(user_instance.username_lowercase, None)


        #set username identical to user1, but check via case insensitive
        response = self.client.post(reverse('users_set_username_api'), data={
            'username': 'uSEr1',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=another_email.lower()
        )

        #expect
        self.assertEqual(user_instance.username, None)
        self.assertEqual(user_instance.username_lowercase, None)

        #set username, but correct
        response = self.client.post(reverse('users_set_username_api'), data={
            'username': 'user2',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=another_email.lower()
        )

        #expect
        self.assertEqual(user_instance.username, 'user2')
        self.assertEqual(user_instance.username_lowercase, 'user2')



class AudioClips_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        pass


    def test_ffmpeg(self):

        #should have webm/opus and mp4/__ files for test, but too lazy for now
        #webm/opus works
        #https://dirask.com/posts/JavaScript-supported-Audio-Video-MIME-Types-by-MediaRecorder-Chrome-and-Firefox-jERn81

        # audio_file = 'audio-clips/year_2023/month_7/day_21/user_id_1/e_13.webm'
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



#not yet adjusted to use FactoryBoy
@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'voicewake/tests'),
)
class CoreProcess_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.users = []

        for x in range(0, 6):

            current_user = get_user_model().objects.create_user(
                username='useR'+str(x),
                email='user'+str(x)+'@gmail.com',
            )

            current_user = get_user_model().objects.get(username_lowercase="user"+str(x))

            current_user.is_active = True
            current_user.save()

            cls.users.append(current_user)

        #audio file
        cls.audio_file_full_path = os.path.join(settings.BASE_DIR, 'voicewake/tests/audio_can_overwrite.mp3')
        cls.audio_file = open(cls.audio_file_full_path, 'rb')
        cls.audio_file = SimpleUploadedFile(cls.audio_file.name, cls.audio_file.read(), 'audio/mp3')

        #dummy file
        cls.dummy_file_full_path = os.path.join(settings.BASE_DIR, 'voicewake/tests/dummy_file.txt')
        cls.dummy_file = open(cls.dummy_file_full_path, 'rb')
        cls.dummy_file = SimpleUploadedFile(cls.dummy_file.name, cls.dummy_file.read(), 'audio/mp3')

        cls.audio_file_path = "/audio_test.mp3"
        cls.audio_volume_peaks = [
            0.32, 0.47, 0.76, 0.75, 0.79, 0.59, 0.78, 0.83, 0.85, 0.77,
            0.62, 0.69, 0.97, 0.96, 0.97, 0.96, 0.96, 0.63, 0.47, 0.0
        ]
        cls.audio_duration_s = 26
        cls.audio_clip_tone = AudioClipTones.objects.first()


    @classmethod
    def tearDownClass(cls):

        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'audio_clips'), ignore_errors=True)

        super().tearDownClass()


    def login(self, user_instance):

        #need this here because @classmethod does not have .client attribute
        self.client.force_login(user_instance)


    def get_audio_file(self):

        #need this to auto-reset via seek(0)
        self.audio_file.seek(0)
        return self.audio_file


    def get_dummy_file(self):

        #need this to auto-reset via seek(0)
        self.dummy_file.seek(0)
        return self.dummy_file


    def create_event(self, created_by, generic_status_name="incomplete"):

        return Events.objects.create(
            event_name="yolo",
            created_by=created_by,
            generic_status=GenericStatuses.objects.get(generic_status_name=generic_status_name)
        )


    def create_audio_clip(
        self,
        user_id:int, event_id:int, audio_clip_role_name:Literal['originator', 'responder'],
        audio_clip_tone_id:int=1,
        generic_status_name:str="ok", is_banned:bool=False,
    ):

        return AudioClips.objects.create(
            user_id=user_id,
            event_id=event_id,
            audio_clip_role=AudioClipRoles.objects.get(audio_clip_role_name=audio_clip_role_name),
            audio_clip_tone_id=audio_clip_tone_id,
            generic_status=GenericStatuses.objects.get(generic_status_name=generic_status_name),
            audio_duration_s=self.audio_duration_s,
            audio_volume_peaks=self.audio_volume_peaks,
            audio_file=self.audio_file_path,
            is_banned=is_banned,
        )


    def create_event_reply_queue(self, event_id:int, locked_for_user_id:int, is_replying:bool, when_locked:datetime):

        return EventReplyQueues.objects.create(
            event_id=event_id,
            locked_for_user_id=locked_for_user_id,
            is_replying=is_replying,
            when_locked=when_locked
        )


    def create_user_event(self, user_id:int, event_id:int, when_excluded_for_reply:datetime):

        return UserEvents.objects.create(
            user_id=user_id,
            event_id=event_id,
            when_excluded_for_reply=when_excluded_for_reply
        )


    def create_user_block(self, user_id:int, blocked_user_id:int):

        return UserBlocks.objects.create(
            user_id=user_id,
            blocked_user_id=blocked_user_id
        )


    def test_create_event_ok(self):

        self.login(self.users[0])

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_events_api'), data)

        self.assertEqual(request.status_code, 201)
        print_function_name(request.content)

        #check data

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertTrue('event_id' in result_data)
        self.assertEqual(Events.objects.all().count(), 1)
        self.assertEqual(AudioClips.objects.all().count(), 1)
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)

        event = Events.objects.first()
        self.assertEqual(event.created_by_id, self.users[0].id)
        self.assertEqual(event.event_name, data['event_name'])

        audio_clip = AudioClips.objects.first()
        self.assertEqual(audio_clip.user_id, self.users[0].id)
        self.assertEqual(audio_clip.audio_clip_tone_id, data['audio_clip_tone_id'])
        self.assertTrue(len(audio_clip.audio_file) > 0)

        #get data via API
        #we want to see what we get for audio_file

        request = self.client.get(reverse('get_events_api', kwargs={'event_id': audio_clip.event.id}))

        self.assertEqual(request.status_code, 200)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        print(result_data)


    def test_create_event_missing_args(self):

        self.login(self.users[0])

        data={
            'audio_clip_tone_id': 1,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_events_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        data={
            'event_name': 'yolo',
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_events_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
        }

        request = self.client.post(reverse('create_events_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #no remnants on failure
        self.assertEqual(Events.objects.all().count(), 0)
        self.assertEqual(AudioClips.objects.all().count(), 0)


    def test_create_event_faulty_args(self):

        self.login(self.users[0])

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 9999999,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_events_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
            'audio_file': self.get_dummy_file(),
        }

        request = self.client.post(reverse('create_events_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #no remnants on failure
        self.assertEqual(Events.objects.all().count(), 0)
        self.assertEqual(AudioClips.objects.all().count(), 0)


    def test_create_event_daily_limit_reached(self):

        self.login(self.users[0])

        with self.settings(EVENT_CREATE_DAILY_LIMIT=1):

            data={
                'event_name': 'yolo',
                'audio_clip_tone_id': 1,
                'audio_file': self.get_audio_file(),
            }

            request = self.client.post(reverse('create_events_api'), data)
            self.assertEqual(request.status_code, 201)
            print_function_name(request.content)

            data={
                'event_name': 'yolo',
                'audio_clip_tone_id': 1,
                'audio_file': self.get_audio_file(),
            }

            request = self.client.post(reverse('create_events_api'), data)
            self.assertEqual(request.status_code, 400)
            print_function_name(request.content)

            #check

            result_data = (bytes(request.content).decode())
            result_data = json.loads(result_data)

            self.assertEqual(result_data['event_create_daily_limit_reached'], True)
            self.assertTrue(Events.objects.count(), 1)
            self.assertTrue(AudioClips.objects.count(), 1)


    def test_list_event_reply_choices_daily_limit_reached(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "completed"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = self.create_audio_clip(
            self.users[1].id,
            sample_event_0.id,
            "responder",
        )

        sample_event_1 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_2 = self.create_audio_clip(
            self.users[0].id,
            sample_event_1.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        with self.settings(EVENT_REPLY_DAILY_LIMIT=1):

            data = {}

            request = self.client.post(reverse('list_event_reply_choices_api'), data)

            self.assertEqual(request.status_code, 400)
            print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(
            EventReplyQueues.objects.filter(
                locked_for_user=self.users[1], event_id=sample_event_1.id, is_replying=False
            ).exists()
        )
        self.assertEqual(result_data['event_reply_daily_limit_reached'], True)
        self.assertEqual(Events.objects.count(), 2)
        self.assertEqual(AudioClips.objects.count(), 3)


    def test_list_reply_choices_first_time_no_unlock(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check data

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)
        result_data = result_data['data'][0]

        self.assertTrue('event' in result_data and type(result_data['event']) == dict)
        self.assertTrue('originator' in result_data and len(result_data['originator']) == 1)
        self.assertTrue('responder' in result_data and len(result_data['responder']) == 0)
        self.assertTrue('event_reply_queue' in result_data and type(result_data['event_reply_queue']) == dict)

        event_reply_queue = EventReplyQueues.objects.first()
        user_event = UserEvents.objects.first()

        self.assertTrue(result_data['event_reply_queue']['when_locked'] is not None)
        self.assertEqual(result_data['event_reply_queue']['is_replying'], event_reply_queue.is_replying)
        self.assertEqual(result_data['event']['id'], event_reply_queue.event_id)
        self.assertEqual(event_reply_queue.locked_for_user_id, self.users[1].id)
        self.assertEqual(UserEvents.objects.all().count(), 1)
        self.assertEqual(user_event.event_id, sample_event_0.id)
        self.assertEqual(user_event.user_id, self.users[1].id)
        self.assertIsNotNone(user_event.when_excluded_for_reply)


    def test_list_reply_choices_first_time_has_unlock(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check data

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)
        result_data = result_data['data'][0]

        self.assertTrue('event' in result_data and type(result_data['event']) == dict)
        self.assertTrue('originator' in result_data and len(result_data['originator']) == 1)
        self.assertTrue('responder' in result_data and len(result_data['responder']) == 0)
        self.assertTrue('event_reply_queue' in result_data and type(result_data['event_reply_queue']) == dict)

        event_reply_queue = EventReplyQueues.objects.first()
        user_event = UserEvents.objects.first()

        self.assertTrue(result_data['event_reply_queue']['when_locked'] is not None)
        self.assertEqual(result_data['event_reply_queue']['is_replying'], event_reply_queue.is_replying)
        self.assertEqual(result_data['event']['id'], event_reply_queue.event_id)
        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertEqual(event_reply_queue.locked_for_user_id, self.users[1].id)
        self.assertEqual(UserEvents.objects.all().count(), 1)
        self.assertEqual(user_event.event_id, sample_event_0.id)
        self.assertEqual(user_event.user_id, self.users[1].id)
        self.assertIsNotNone(user_event.when_excluded_for_reply)


    def test_list_reply_choices_ensure_own_events_not_listed(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[0])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)
        result_data = result_data['data']

        self.assertEqual(result_data, [])
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(UserEvents.objects.all().count(), 0)


    def test_list_reply_choices_where_originator_is_blocked(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        user_block_0 = self.create_user_block(user_id=self.users[1].id, blocked_user_id=self.users[0].id)

        #start

        #list event

        self.login(self.users[1])

        request = self.client.post(reverse('list_event_reply_choices_api'))

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check data

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)
        result_data = result_data['data']

        self.assertEqual(result_data, [])
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(UserEvents.objects.all().count(), 0)


    def test_list_reply_choices_where_responder_is_blocked(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        user_block_0 = self.create_user_block(user_id=self.users[0].id, blocked_user_id=self.users[1].id)

        #start

        #list event

        self.login(self.users[1])

        request = self.client.post(reverse('list_event_reply_choices_api'))

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check data

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)
        result_data = result_data['data']

        self.assertEqual(len(result_data), 0)
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(UserEvents.objects.all().count(), 0)


    def test_list_reply_choices_has_something_locked_no_unlock(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #ensure when_locked does not change
        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=10))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_1 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_1 = self.create_audio_clip(
            self.users[0].id,
            sample_event_1.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(sample_event_0.id, result_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 1)
        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertEqual(EventReplyQueues.objects.first().id, sample_event_reply_queue_0.id)
        self.assertEqual(EventReplyQueues.objects.first().when_locked, sample_event_reply_queue_0.when_locked)


    def test_list_reply_choices_has_something_locked_has_unlock(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #simply ensure when_locked changes
        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=10))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_1 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_1 = self.create_audio_clip(
            self.users[0].id,
            sample_event_1.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=result_data['data'][0]['event']['id'])

        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertNotEqual(EventReplyQueues.objects.first().id, result_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 2)
        self.assertEqual(new_user_event.event_id, sample_event_1.id)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)
        self.assertNotEqual(EventReplyQueues.objects.first().when_locked, sample_event_reply_queue_0.when_locked)


    def test_list_reply_choices_has_something_locked_but_expired_no_unlock(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_CHOICE_MAX_DURATION_S * 2)))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_1 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_1 = self.create_audio_clip(
            self.users[0].id,
            sample_event_1.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=result_data['data'][0]['event']['id'])

        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertNotEqual(EventReplyQueues.objects.first().id, result_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 2)
        self.assertEqual(new_user_event.event_id, sample_event_1.id)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)


    def test_list_reply_choices_has_something_locked_but_expired_has_unlock(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_CHOICE_MAX_DURATION_S * 2)))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_1 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_1 = self.create_audio_clip(
            self.users[0].id,
            sample_event_1.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=result_data['data'][0]['event']['id'])

        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertNotEqual(EventReplyQueues.objects.first().id, result_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 2)
        self.assertEqual(new_user_event.event_id, sample_event_1.id)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)


    def test_start_reply_ok(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=sample_event_0.id)

        self.assertTrue(event_reply_queue.is_replying)
        self.assertEqual(result_data['data'][0]['event_id'], event_reply_queue.event_id)
        self.assertEqual(
            datetime.strptime(result_data['data'][0]['when_locked'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=ZoneInfo('UTC')),
            event_reply_queue.when_locked
        )
        self.assertEqual(result_data['data'][0]['is_replying'], event_reply_queue.is_replying)


    def test_start_reply_with_missing_args(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=sample_event_0.id)

        self.assertFalse(event_reply_queue.is_replying)


    def test_start_reply_with_faulty_args(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'event_id': 9999}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=sample_event_0.id)

        self.assertFalse(event_reply_queue.is_replying)


    def test_list_new_event_with_started_reply_no_unlock(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(sample_event_0.id, result_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 1)
        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertEqual(EventReplyQueues.objects.first().id, sample_event_reply_queue_0.id)


    def test_list_new_event_with_started_reply_has_unlock(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_1 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_1 = self.create_audio_clip(
            self.users[0].id,
            sample_event_1.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertNotEqual(sample_event_0.id, result_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 2)
        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertNotEqual(EventReplyQueues.objects.first().id, sample_event_reply_queue_0.id)


    def test_start_reply_but_never_queued(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)


    def test_start_reply_but_expired(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_CHOICE_MAX_DURATION_S) * 2))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(result_data['can_retry'])
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(
            UserEvents.objects.filter(
                user=self.users[1],
                event_id=sample_event_0,
                when_excluded_for_reply__isnull=False
            ).count(),
            1
        )


    def test_start_reply_but_event_is_banned(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "deleted"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
            generic_status_name="deleted",
            is_banned=True,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(result_data['can_retry'])
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(
            UserEvents.objects.filter(
                user=self.users[1],
                event_id=sample_event_0,
                when_excluded_for_reply__isnull=False
            ).count(),
            1
        )


    def test_start_reply_for_someone_else(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[2].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[2].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        event_reply_queue = EventReplyQueues.objects.get(event_id=sample_event_0.id, locked_for_user=self.users[2])

        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertEqual(
            UserEvents.objects.filter(
                user=self.users[2],
                event_id=sample_event_0,
                when_excluded_for_reply__isnull=False
            ).count(),
            1
        )
        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1]).exists())
        self.assertFalse(UserEvents.objects.filter(user=self.users[1]).exists())


    def test_create_reply_ok(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 201)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 2)
        self.assertEqual(
            AudioClips.objects.filter(
                user_id=self.users[1].id,
                event_id=sample_event_0.id,
                audio_clip_role__audio_clip_role_name='responder',
                audio_clip_tone=self.audio_clip_tone
            ).count(),
            1
        )


    def test_create_reply_with_missing_args(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        data = {
            'event_id': sample_event_0.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': self.audio_clip_tone.id,
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_create_reply_with_faulty_args(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': 99999,
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 99999,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_dummy_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_create_reply_but_never_queued_for_it(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_create_reply_locked_but_not_replying(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertTrue(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)


    def test_create_reply_for_someone_else(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[2].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[2].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertTrue(EventReplyQueues.objects.filter(locked_for_user=self.users[2], event_id=sample_event_0.id).exists())
        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)


    def test_create_reply_but_expired(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_MAX_DURATION_S * 2)))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(result_data['can_retry'])
        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertEqual(AudioClips.objects.filter(user_id=self.users[1].id).count(), 0)
        self.assertEqual(UserEvents.objects.filter(user_id=self.users[1].id).count(), 1)
        sample_event_0.refresh_from_db()
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')


    def test_create_reply_but_event_is_banned(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "deleted"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
            generic_status_name="deleted",
            is_banned=True,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(result_data['can_retry'])
        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertEqual(AudioClips.objects.filter(user_id=self.users[1].id).count(), 0)
        self.assertEqual(UserEvents.objects.filter(user_id=self.users[1].id).count(), 1)


    def test_cancel_reply_ok(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())


    def test_cancel_reply_with_missing_args(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_cancel_reply_with_faulty_args(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': 9999,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_cancel_reply_but_never_queued_for_it(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_cancel_reply_locked_but_not_replying(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())


    def test_cancel_reply_for_someone_else(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[2].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[2].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertTrue(EventReplyQueues.objects.filter(locked_for_user=self.users[2], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[2], event_id=sample_event_0.id).exists())


    def test_cancel_reply_but_event_is_banned(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "deleted"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
            generic_status_name="deleted",
            is_banned=True,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())


    def test_create_audio_clip_report_ok(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertIsNone(audio_clip_report.last_evaluated)


    def test_create_audio_clip_report_missing_args(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 0)


    def test_create_audio_clip_report_faulty_args(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {
            'yolo': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 0)


    def test_create_audio_clip_report_not_found(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': 9999999
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 0)


    def test_create_audio_clip_report_already_reported_before(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            audio_clip_id=sample_audio_clip_0.id
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertIsNone(audio_clip_report.last_evaluated)


    def test_create_audio_clip_report_already_banned(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
            is_banned=True,
        )

        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            audio_clip_id=sample_audio_clip_0.id,
            last_evaluated=get_datetime_now(),
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertIsNotNone(audio_clip_report.last_evaluated)


    def test_create_audio_clip_report_self_ok(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[0])

        data = {
            'audio_clip_id': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertIsNone(audio_clip_report.last_evaluated)


    def test_create_user_block_ok(self):

        self.login(self.users[1])

        data = {
            'username': self.users[0].username,
            'to_block': True
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(UserBlocks.objects.all().count(), 1)


    def test_create_user_block_missing_args(self):

        self.login(self.users[1])

        #start

        data = {
            'username': self.users[0].username,
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        #200 because bool defaults to False when not passed
        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(UserBlocks.objects.all().count(), 0)

        #start

        data = {
            'to_block': True,
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(UserBlocks.objects.all().count(), 0)


    def test_create_user_block_faulty_args(self):

        self.login(self.users[1])

        #start

        data = {
            'username': self.users[0].username,
            'to_block': '',
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        #200 because bool defaults to False when not passed
        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(UserBlocks.objects.all().count(), 0)


    def test_create_user_block_unblock_ok(self):

        sample_user_block_0 = UserBlocks.objects.create(
            user_id=self.users[1].id,
            blocked_user_id=self.users[0].id
        )

        self.login(self.users[1])

        data = {
            'username': self.users[0].username,
            'to_block': False
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(UserBlocks.objects.all().count(), 0)


    def test_audio_clip_like_dislike_missing_args(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        #bool defaults to False by serializer
        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        data = {
            'is_liked': True,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_audio_clip_like_dislike_faulty_args(self):


        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        #0 and 1 are considered as valid bool by DRF serializer
        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': 1,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': 2,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        data = {
            'audio_clip_id': 999,
            'is_liked': True,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_create_and_delete_audio_clip_like(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        sample_audio_clip_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 1)
        self.assertEqual(sample_audio_clip_0.like_ratio, 1)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertTrue(audio_clip_like_dislike.is_liked)

        #undo

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': json.dumps(None)
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        sample_audio_clip_0.refresh_from_db()
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)


    def test_create_and_delete_audio_clip_dislike(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': False
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        sample_audio_clip_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 1)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertFalse(audio_clip_like_dislike.is_liked)

        #undo

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': json.dumps(None)
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        sample_audio_clip_0.refresh_from_db()
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)


    def test_random_audio_clip_like_dislike_chaining(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        #start

        self.login(self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        sample_audio_clip_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 1)
        self.assertEqual(sample_audio_clip_0.like_ratio, 1)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertTrue(audio_clip_like_dislike.is_liked)

        #switch

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': False
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        sample_audio_clip_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 1)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertFalse(audio_clip_like_dislike.is_liked)

        #switch again

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        sample_audio_clip_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 1)
        self.assertEqual(sample_audio_clip_0.like_ratio, 1)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertTrue(audio_clip_like_dislike.is_liked)

        #random resiliency test
        #reset to None

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': json.dumps(None)
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        sample_audio_clip_0.refresh_from_db()
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)

        #like

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        sample_audio_clip_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 1)
        self.assertEqual(sample_audio_clip_0.like_ratio, 1)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertTrue(audio_clip_like_dislike.is_liked)


    def test_random_audio_clip_like_dislike_chaining_multiple_users(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        def do_request(target_user, is_liked:bool|None):

            self.login(target_user)

            data = {
                'audio_clip_id': sample_audio_clip_0.id,
                'is_liked': json.dumps(is_liked)
            }

            request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

            self.assertEqual(request.status_code, 200)

        #we randomise between True/False/None, among users
        #we then track it and see if db accurately reflects it

        possible_is_liked_values = [True, False, None]

        users_latest_is_liked = {}

        for user in self.users:

            users_latest_is_liked.update({
                user.id: None
            })

        #start

        for test_loop in range(0, 10):

            #randomise is_liked and make request for every user

            for user in self.users:

                is_liked = possible_is_liked_values[random.randint(0, 2)]

                do_request(user, is_liked)

                users_latest_is_liked.update({
                    user.id: is_liked
                })

        #check

        sample_audio_clip_0.refresh_from_db()

        audio_clip_likes_dislikes = AudioClipLikesDislikes.objects.all()

        is_liked_total_count = {
            'true': 0,
            'false': 0,
        }

        for row in audio_clip_likes_dislikes:

            if row.is_liked is True:
                is_liked_total_count['true'] += 1
            elif row.is_liked is False:
                is_liked_total_count['false'] += 1

            if row.is_liked != users_latest_is_liked[row.user_id]:

                raise AssertionError('is_liked did not match.')

        self.assertEqual(sample_audio_clip_0.like_count, is_liked_total_count['true'])
        self.assertEqual(sample_audio_clip_0.dislike_count, is_liked_total_count['false'])


    def test_cronjob_ban_audio_clip_originator_ok(self):

        datetime_now = get_datetime_now()

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_audio_clip_0.like_count = 2
        sample_audio_clip_0.dislike_count = 10
        sample_audio_clip_0.like_ratio = 0.2
        sample_audio_clip_0.save()

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        #start

        with self.settings(
            BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
            BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
            BAN_AUDIO_CLIP_MIN_AGE_S=11
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, 1)


    def test_cronjob_ban_audio_clip_responder_ok(self):

        datetime_now = get_datetime_now()

        sample_event_0 = self.create_event(
            self.users[0],
            "completed"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_audio_clip_1 = self.create_audio_clip(
            self.users[1].id,
            sample_event_0.id,
            "responder",
        )

        sample_audio_clip_1.like_count = 2
        sample_audio_clip_1.dislike_count = 10
        sample_audio_clip_1.like_ratio = 0.2
        sample_audio_clip_1.save()

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_1.id,
        )

        #start

        with self.settings(
            BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
            BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
            BAN_AUDIO_CLIP_MIN_AGE_S=11
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[1].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertTrue(self.users[1].banned_until > datetime_now)
        self.assertEqual(self.users[1].ban_count, 1)


    def test_cronjob_ban_audio_clip_same_event_all_users(self):

        datetime_now = get_datetime_now()

        sample_event_0 = self.create_event(
            self.users[0],
            "completed"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_audio_clip_0.like_count = 2
        sample_audio_clip_0.dislike_count = 10
        sample_audio_clip_0.like_ratio = 0.2
        sample_audio_clip_0.save()

        sample_audio_clip_1 = self.create_audio_clip(
            self.users[1].id,
            sample_event_0.id,
            "responder",
        )

        sample_audio_clip_1.like_count = 2
        sample_audio_clip_1.dislike_count = 10
        sample_audio_clip_1.like_ratio = 0.2
        sample_audio_clip_1.save()

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )
        sample_audio_clip_report_1 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_1.id,
        )

        #start

        with self.settings(
            BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
            BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
            BAN_AUDIO_CLIP_MIN_AGE_S=11
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        sample_audio_clip_report_1.refresh_from_db()
        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertTrue(sample_audio_clip_report_1.last_evaluated >= sample_audio_clip_report_1.last_reported)
        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertTrue(self.users[1].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, 1)
        self.assertEqual(self.users[1].ban_count, 1)


    def test_cronjob_ban_audio_clip_different_event_different_users(self):

        datetime_now = get_datetime_now()

        #event 0, ban originator

        sample_event_0 = self.create_event(
            self.users[0],
            "completed"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_audio_clip_1 = self.create_audio_clip(
            self.users[1].id,
            sample_event_0.id,
            "responder",
        )

        sample_audio_clip_0.like_count = 2
        sample_audio_clip_0.dislike_count = 10
        sample_audio_clip_0.like_ratio = 0.2
        sample_audio_clip_0.save()

        #event 1, ban responder

        sample_event_1 = self.create_event(
            self.users[0],
            "completed"
        )

        sample_audio_clip_2 = self.create_audio_clip(
            self.users[0].id,
            sample_event_1.id,
            "originator",
        )

        sample_audio_clip_3 = self.create_audio_clip(
            self.users[1].id,
            sample_event_1.id,
            "responder",
        )

        sample_audio_clip_3.like_count = 2
        sample_audio_clip_3.dislike_count = 10
        sample_audio_clip_3.like_ratio = 0.2
        sample_audio_clip_3.save()

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )
        sample_audio_clip_report_1 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_3.id,
        )

        #start

        with self.settings(
            BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
            BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
            BAN_AUDIO_CLIP_MIN_AGE_S=11
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_event_1.refresh_from_db()
        sample_audio_clip_2.refresh_from_db()
        sample_audio_clip_3.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        sample_audio_clip_report_1.refresh_from_db()
        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_1.is_banned)

        self.assertEqual(sample_event_1.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_2.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_2.is_banned)
        self.assertEqual(sample_audio_clip_3.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_3.is_banned)

        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertTrue(sample_audio_clip_report_1.last_evaluated >= sample_audio_clip_report_1.last_reported)

        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertTrue(self.users[1].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, 1)
        self.assertEqual(self.users[1].ban_count, 1)


    def test_cronjob_ban_audio_clip_different_event_same_user(self):

        datetime_now = get_datetime_now()

        #event 0, ban originator

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_audio_clip_0.like_count = 2
        sample_audio_clip_0.dislike_count = 10
        sample_audio_clip_0.like_ratio = 0.2
        sample_audio_clip_0.save()

        #event 1, ban responder

        sample_event_1 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_1 = self.create_audio_clip(
            self.users[0].id,
            sample_event_1.id,
            "originator",
        )

        sample_audio_clip_1.like_count = 2
        sample_audio_clip_1.dislike_count = 10
        sample_audio_clip_1.like_ratio = 0.2
        sample_audio_clip_1.save()

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )
        sample_audio_clip_report_1 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_1.id,
        )

        #start

        with self.settings(
            BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
            BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
            BAN_AUDIO_CLIP_MIN_AGE_S=11
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_event_1.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        sample_audio_clip_report_1.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)

        self.assertEqual(sample_event_1.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)

        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertTrue(sample_audio_clip_report_1.last_evaluated >= sample_audio_clip_report_1.last_reported)

        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, 2)


    def test_cronjob_ban_audio_clip_skip_not_reported(self):

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_audio_clip_0.like_count = 2
        sample_audio_clip_0.dislike_count = 10
        sample_audio_clip_0.like_ratio = 0.2
        sample_audio_clip_0.save()

        #start

        with self.settings(
            BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
            BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
            BAN_AUDIO_CLIP_MIN_AGE_S=11
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_0.is_banned)
        self.assertIsNone(self.users[0].banned_until)


    def test_cronjob_ban_audio_clip_skip_already_evaluated(self):

        datetime_now = get_datetime_now()

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_audio_clip_0.like_count = 2
        sample_audio_clip_0.dislike_count = 10
        sample_audio_clip_0.like_ratio = 0.2
        sample_audio_clip_0.save()

        #arbitrary last_evaluated, as long as > last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now + timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        previous_last_evaluated = sample_audio_clip_report_0.last_evaluated

        #start

        with self.settings(
            BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
            BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
            BAN_AUDIO_CLIP_MIN_AGE_S=11
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_0.is_banned)
        self.assertEqual(previous_last_evaluated, sample_audio_clip_report_0.last_evaluated)
        self.assertIsNone(self.users[0].banned_until)


    def test_cronjob_ban_audio_clip_skip_already_banned(self):

        datetime_now = get_datetime_now()

        sample_event_0 = self.create_event(
            self.users[0],
            "deleted"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
            generic_status_name='deleted',
            is_banned=True,
        )

        sample_audio_clip_0.like_count = 2
        sample_audio_clip_0.dislike_count = 10
        sample_audio_clip_0.like_ratio = 0.2
        sample_audio_clip_0.save()

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        previous_last_evaluated = sample_audio_clip_report_0.last_evaluated

        #start

        with self.settings(
            BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
            BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
            BAN_AUDIO_CLIP_MIN_AGE_S=11
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(previous_last_evaluated, sample_audio_clip_report_0.last_evaluated)
        self.assertIsNone(self.users[0].banned_until)


    def test_cronjob_reset_reply_choice_ok(self):

        datetime_now = get_datetime_now()

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            sample_event_0.id,
            self.users[1].id,
            False,
            (datetime_now - timedelta(seconds=10))
        )

        with self.settings(
            EVENT_REPLY_CHOICE_MAX_DURATION_S=2,
        ):

            cronjob_reset_event_reply_choice_overdue()

        self.assertFalse(EventReplyQueues.objects.filter(event_id=sample_event_0.id).exists())


    def test_cronjob_reset_reply_choice_not_expired(self):

        datetime_now = get_datetime_now()

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            sample_event_0.id,
            self.users[1].id,
            False,
            (datetime_now - timedelta(seconds=10))
        )

        with self.settings(
            EVENT_REPLY_CHOICE_MAX_DURATION_S=20,
        ):

            cronjob_reset_event_reply_choice_overdue()

        self.assertTrue(EventReplyQueues.objects.filter(event_id=sample_event_0.id).exists())


    def test_cronjob_reset_reply_choice_skip_unrelated_expired_rows(self):

        datetime_now = get_datetime_now()

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            sample_event_0.id,
            self.users[1].id,
            True,
            (datetime_now - timedelta(seconds=10))
        )

        with self.settings(
            EVENT_REPLY_CHOICE_MAX_DURATION_S=2,
        ):

            cronjob_reset_event_reply_choice_overdue()

        self.assertTrue(EventReplyQueues.objects.filter(event_id=sample_event_0.id).exists())


    def test_cronjob_reset_reply_ok(self):

        datetime_now = get_datetime_now()

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            sample_event_0.id,
            self.users[1].id,
            True,
            (datetime_now - timedelta(seconds=10))
        )

        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=2,
        ):

            cronjob_reset_event_reply_overdue()

        self.assertFalse(EventReplyQueues.objects.filter(event_id=sample_event_0.id).exists())


    def test_cronjob_reset_reply_not_expired(self):

        datetime_now = get_datetime_now()

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            sample_event_0.id,
            self.users[1].id,
            True,
            (datetime_now - timedelta(seconds=10))
        )

        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=20,
        ):

            cronjob_reset_event_reply_overdue()

        self.assertTrue(EventReplyQueues.objects.filter(event_id=sample_event_0.id).exists())


    def test_cronjob_reset_reply_skip_unrelated_expired_rows(self):

        datetime_now = get_datetime_now()

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            sample_event_0.id,
            self.users[1].id,
            False,
            (datetime_now - timedelta(seconds=10))
        )

        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=2,
        ):

            cronjob_reset_event_reply_overdue()

        self.assertTrue(EventReplyQueues.objects.filter(event_id=sample_event_0.id).exists())
















































