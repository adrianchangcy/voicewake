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
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_SECONDS, settings.TOTP_TOLERANCE_SECONDS,
            0, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_SECONDS,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_SECONDS
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
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_SECONDS, settings.TOTP_TOLERANCE_SECONDS,
            0, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_SECONDS,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_SECONDS
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


    def test_prepare_test_data(self):

        prepare_test_data_class = PrepareTestData(for_test=True)

        prepare_test_data_class.do_quick_start(1)


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

        #check size, not included in HandleAudioFile
        self.assertLessEqual(audio_file_in_memory.size, settings.AUDIO_CLIP_MAX_FILE_SIZE_BYTES)

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



class Random_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        pass


    def test_random(self):

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


    def test_like_dislike_and_trigger(self):

        self.login(self.user_1_instance)

        #create user2 audio_clip
        prepare_test_data_class = PrepareTestData(for_test=True)
        prepare_test_data_class.prepare_test_data_events(
            self.user_1_username,
            self.user_2_username,
            0,
            1
        )

        def do_like_dislike(audio_clip_id, is_liked, previous_is_liked=None):

            #get initial audio_clip to evaluate trigger on like_count and dislike_count
            target_audio_clip = AudioClips.objects.get(pk=audio_clip_id)

            #submit
            request = self.client.post(
                path=reverse('audio_clip_likes_dislikes_api'),
                data={
                    'audio_clip_id': audio_clip_id,
                    'is_liked': is_liked
                },
                content_type='application/json'
            )

            #expect success
            self.assertEqual(request.status_code, 200)

            #check db
            try:

                audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(audio_clip_id=audio_clip_id, user_id=self.user_1_instance.id)
                self.assertEqual(audio_clip_like_dislike.is_liked, is_liked)

            except AudioClipLikesDislikes.DoesNotExist:

                self.assertEqual(is_liked, None)

            expected_like_count = target_audio_clip.like_count
            expected_dislike_count = target_audio_clip.dislike_count

            #check count trigger
            updated_target_audio_clip = AudioClips.objects.get(pk=audio_clip_id)

            if is_liked == previous_is_liked:

                #do nothing if identical
                pass

            elif previous_is_liked is True:

                #is_liked will not be True
                expected_like_count -= 1
                if is_liked is False:
                    expected_dislike_count += 1

            elif previous_is_liked is False:

                #is_liked will not be False
                expected_dislike_count -= 1
                if is_liked is True:
                    expected_like_count += 1

            else:
                
                #is_liked will not be None
                if is_liked is True:
                    expected_like_count += 1
                else:
                    expected_dislike_count += 1

            #evaluate
            self.assertEqual(updated_target_audio_clip.like_count, expected_like_count)
            self.assertEqual(updated_target_audio_clip.dislike_count, expected_dislike_count)


        #get any audio_clip
        first_audio_clip = AudioClips.objects.first()

        #check like/dislike doesn't exist for current user
        self.assertFalse(
            AudioClipLikesDislikes.objects.filter(
                audio_clip_id=first_audio_clip.id, user_id=self.user_1_instance.id
            ).exists()
        )

        #do request, and try repeating for resiliency
        do_like_dislike(audio_clip_id=first_audio_clip.id, is_liked=True, previous_is_liked=None)
        do_like_dislike(audio_clip_id=first_audio_clip.id, is_liked=True, previous_is_liked=True)

        #switch to dislike, also repeat
        do_like_dislike(audio_clip_id=first_audio_clip.id, is_liked=False, previous_is_liked=True)
        do_like_dislike(audio_clip_id=first_audio_clip.id, is_liked=False, previous_is_liked=False)

        #remove, and repeat
        do_like_dislike(audio_clip_id=first_audio_clip.id, is_liked=None, previous_is_liked=False)
        do_like_dislike(audio_clip_id=first_audio_clip.id, is_liked=None, previous_is_liked=None)


    def test_user_block(self):

        self.login(self.user_1_instance)

        def do_block(to_block:bool):

            #block
            request = self.client.post(
                path=reverse('user_blocks_api'),
                data={
                    'username': self.user_2_username,
                    'to_block': to_block
                }
            )

            #expect success
            self.assertEqual(request.status_code, 200)

            self.assertEqual(UserBlocks.objects.filter(user=self.user_1_instance, blocked_user=self.user_2_instance).exists(), to_block)

        #block
        do_block(True)

        #block again, expect no change
        do_block(True)

        #unblock, expect no row
        do_block(False)


    def test_audio_clip_report(self):

        self.login(self.user_1_instance)

        #create user2 audio_clip
        prepare_test_data_class = PrepareTestData(for_test=True)
        prepare_test_data_class.prepare_test_data_events(
            self.user_1_username,
            self.user_2_username,
            0,
            1
        )

        #get audio_clips from events that both users are involved in
        linked_audio_clips = AudioClips.objects.raw(
            '''
                WITH
                    user_1_events AS (
                        SELECT events.id FROM events
                        INNER JOIN audio_clips ON events.id = audio_clips.event_id
                        WHERE audio_clips.user_id = %s
                    ),
                    user_2_events AS (
                        SELECT events.id FROM events
                        INNER JOIN audio_clips ON events.id = audio_clips.event_id
                        WHERE audio_clips.user_id = %s
                    ),
                    shared_events AS (
                        SELECT events.id FROM events
                        RIGHT JOIN user_1_events ON events.id = user_1_events.id
                        RIGHT JOIN user_2_events ON events.id = user_2_events.id
                    )
                    SELECT audio_clips.* FROM audio_clips
                    RIGHT JOIN shared_events ON audio_clips.event_id = shared_events.id
            ''',
            params=(
                self.user_1_instance.id,
                self.user_2_instance.id
            )
        )

        #report the other audio_clip that does not belong to this signed in user
        audio_clip_to_report = None

        for row in linked_audio_clips:

            if row.user_id != self.user_1_instance.id:

                audio_clip_to_report = row
                break

        #we change audio_clip's values to meet ban conditions
        audio_clip_to_report.like_count = 25
        audio_clip_to_report.dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT * 2
        audio_clip_to_report.when_created = get_datetime_now() - timedelta(seconds=settings.BAN_AUDIO_CLIP_AGE_SECONDS * 2)
        audio_clip_to_report.save()

        #no reports initially
        self.assertEqual(AudioClipReports.objects.count(), 0)

        #report
        result = self.client.post(
            path=reverse('create_audio_clip_reports_api'),
            data={
                'reported_audio_clip_id': audio_clip_to_report.id
            }
        )
        self.assertEqual(result.status_code, 200)

        #check whether report now exists
        self.assertTrue(AudioClipReports.objects.filter(user_id=self.user_1_instance.id, reported_audio_clip_id=audio_clip_to_report.id).exists())

        #try report again, expect to be fine but not accept duplicates
        result = self.client.post(
            path=reverse('create_audio_clip_reports_api'),
            data={
                'reported_audio_clip_id': audio_clip_to_report.id
            }
        )
        self.assertEqual(result.status_code, 200)

        #check whether report now exists
        self.assertTrue(AudioClipReports.objects.filter(user_id=self.user_1_instance.id, reported_audio_clip_id=audio_clip_to_report.id).exists())


    def test_ban(self):

        self.prepare_test_data_class.prepare_test_data_for_bans(
            target_username=self.user_1_username,
            backup_username=self.user_2_username,
            audio_clips_to_ban_quantity=10,
            audio_clips_not_to_ban_quantity=6,
            reporting_user_quantity=10
        )

        #do ban
        cronjob_ban_audio_clips()

        self.assertEqual(AudioClips.objects.filter(is_banned=True).count(), 10)
        self.assertEqual(AudioClipReports.objects.count(), 0)


    def test_audio_clip_tone_trigger(self):

        #pass in audio_clip_tone_slug
        #fetches the row if exists, else fetches all rows
        yolo = AudioClips.objects.raw("SELECT * FROM get_id_of_one_or_all_audio_clip_tones_via_slug(%s)", params=('',))

        #check
        print(str(len(yolo)) + " audio_clip_tones found")
        self.assertGreater(len(yolo), 1)

        yolo = AudioClips.objects.raw("SELECT * FROM get_id_of_one_or_all_audio_clip_tones_via_slug(%s)", params=('smile',))

        #check
        print(str(len(yolo)) + " audio_clip_tones found")
        self.assertEqual(len(yolo), 1)














































