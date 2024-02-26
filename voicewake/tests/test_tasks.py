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
import sys
import shutil
import math
import subprocess
import traceback
import inspect, sys
import dotenv
import logging

import boto3
import argparse
from botocore.exceptions import ClientError
import requests



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
        cls.audio_file_full_path = os.path.join(settings.BASE_DIR, 'voicewake/tests/test_file_samples/audio_can_overwrite.mp3')
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


    def test_cronjob_ban_audio_clip_originator_ok(self):

        datetime_now = get_datetime_now()

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
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
































