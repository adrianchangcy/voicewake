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
from django.db.models import Count

#apps
from voicewake.services import *
from voicewake.models import *
from voicewake.cronjobs import *
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


    def test_ffmpeg(self):

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


class System_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user_1_email = "someemail@gmail.com"
        cls.user_1_username = "someemail"
        cls.user_1_password = "abc"

        cls.user_2_email = "someemail2@gmail.com"
        cls.user_2_username = "someemail2"
        cls.user_2_password = "abc2"

        #prepare data
        #we put it here so that our new account below is not involved
        cls.prepare_test_data_class = PrepareTestData(for_test=True)
        cls.prepare_test_data_class.do_quick_start(1)

        #sign up
        #API already works, as tested in other test cases
        get_user_model().objects.create_user(cls.user_1_email, cls.user_1_username)
        get_user_model().objects.create_user(cls.user_2_email, cls.user_2_username)

        #we do set_unusable_password() for normal users
        #but we need username + password to sign in here, so we set normal password
        cls.user_1_instance = get_user_model().objects.get(email=cls.user_1_email)
        cls.user_2_instance = get_user_model().objects.get(email=cls.user_2_email)

        #set is_active=True for login success
        cls.user_1_instance.is_active = True
        cls.user_1_instance.save()
        cls.user_1_instance.refresh_from_db()

        cls.user_2_instance.is_active = True
        cls.user_2_instance.save()
        cls.user_2_instance.refresh_from_db()


    def login(self, user_instance):

        #need this here because @classmethod does not have .client attribute
        self.client.force_login(user_instance)


    def test_like_dislike(self):

        self.login()

        def do_like_dislike(event_id, is_liked):

            #submit
            request = self.client.post(
                path=reverse('event_likes_dislikes'),
                data={
                    'event_id': event_id,
                    'is_liked': is_liked
                },
                content_type='application/json'
            )

            #expect success
            self.assertEqual(request.status_code, 200)

            #check db
            try:
                event_like_dislike = EventLikesDislikes.objects.get(event_id=first_event.id, user_id=self.user_instance.id)
                self.assertEqual(event_like_dislike.is_liked, is_liked)
            except EventLikesDislikes.DoesNotExist:
                print('event_likes_dislikes record removed')

        #get any event
        first_event = Events.objects.first()

        #check like/dislike doesn't exist for current user
        self.assertFalse(
            EventLikesDislikes.objects.filter(
                event_id=first_event.id, user_id=self.user_instance.id
            ).exists()
        )

        #do request, and try repeating for resiliency
        do_like_dislike(event_id=first_event.id, is_liked=True)
        do_like_dislike(event_id=first_event.id, is_liked=True)

        #switch to dislike, also repeat
        do_like_dislike(event_id=first_event.id, is_liked=False)
        do_like_dislike(event_id=first_event.id, is_liked=False)

        #remove, and repeat
        do_like_dislike(event_id=first_event.id, is_liked=None)
        do_like_dislike(event_id=first_event.id, is_liked=None)


    def test_user_block(self):

        self.login(self.user_1_instance)

        self.client.post(
            path=reverse('users_block_users'),
            data={
                'blocked_user_id': self.user_2_instance.id,
                'to_block': True
            }
        )

        self.assertTrue(UserBlocks.objects.filter(user_id=self.user_1_instance, blocked_user_id=self.user_2_instance).exists())

        #here, you run event_rooms querysets to validate that blocked users don't show up



    def test_event_report(self):

        self.login(self.user_1_instance)

        #create user2 event
        prepare_test_data_class = PrepareTestData(for_test=True)
        prepare_test_data_class.prepare_test_data_event_rooms(
            self.user_1_username,
            self.user_2_username,
            0,
            1
        )

        #get events from event_rooms that both users are involved in
        linked_events = Events.objects.raw(
            '''
                WITH
                    user_1_event_rooms AS (
                        SELECT event_rooms.id FROM event_rooms
                        INNER JOIN events ON event_rooms.id = events.event_room_id
                        WHERE events.user_id = %s
                    ),
                    user_2_event_rooms AS (
                        SELECT event_rooms.id FROM event_rooms
                        INNER JOIN events ON event_rooms.id = events.event_room_id
                        WHERE events.user_id = %s
                    ),
                    shared_event_rooms AS (
                        SELECT event_rooms.id FROM event_rooms
                        RIGHT JOIN user_1_event_rooms ON event_rooms.id = user_1_event_rooms.id
                        RIGHT JOIN user_2_event_rooms ON event_rooms.id = user_2_event_rooms.id
                    )
                    SELECT events.* FROM events
                    RIGHT JOIN shared_event_rooms ON events.event_room_id = shared_event_rooms.id
            ''',
            params=(
                self.user_1_instance.id,
                self.user_2_instance.id
            )
        )

        #report the other event that does not belong to this signed in user
        event_to_report = None

        for row in linked_events:

            if row.user_id != self.user_1_instance.id:

                event_to_report = row
                break

        #we change event's values to meet ban conditions
        event_to_report.like_count = 25
        event_to_report.dislike_count = settings.BAN_EVENT_DISLIKE_COUNT * 2
        event_to_report.when_created = get_datetime_now() - timedelta(seconds=settings.BAN_EVENT_AGE_SECONDS * 2)
        event_to_report.save()

        #no reports initially
        self.assertEqual(EventReports.objects.count(), 0)

        #report
        result = self.client.post(
            path=reverse('create_event_reports'),
            data={
                'reported_event_id': event_to_report.id
            }
        )
        self.assertEqual(result.status_code, 200)

        #check whether report now exists
        self.assertTrue(EventReports.objects.filter(user_id=self.user_1_instance.id, reported_event_id=event_to_report.id).exists())

        #try report again, expect to be fine but not accept duplicates
        result = self.client.post(
            path=reverse('create_event_reports'),
            data={
                'reported_event_id': event_to_report.id
            }
        )
        self.assertEqual(result.status_code, 200)

        #check whether report now exists
        self.assertTrue(EventReports.objects.filter(user_id=self.user_1_instance.id, reported_event_id=event_to_report.id).exists())


    def test_ban(self):

        self.prepare_test_data_class.prepare_test_data_for_bans(
            username=self.user_1_username,
            event_quantity=10,
            reporting_user_quantity=10
        )

        #do ban
        cronjob_ban_events()

        self.assertEqual(Events.objects.filter(is_banned=True).count(), 10)
        self.assertEqual(EventReports.objects.count(), 0)














































