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
from django.core.cache import cache

#apps
from voicewake.services import *
from voicewake.models import *
from voicewake.cronjobs import *
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
class Core_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.datetime_now = get_datetime_now()

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
        cls.audio_file_full_path = os.path.join(settings.BASE_DIR, 'voicewake/tests/file_samples/audio_can_overwrite.mp3')
        cls.audio_file = open(cls.audio_file_full_path, 'rb')
        cls.audio_file = SimpleUploadedFile(cls.audio_file.name, cls.audio_file.read(), 'audio/mp3')

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

        try:
            cache.clear()
        except:
            pass

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


    def test_cronjob_ban_audio_clips__originator_ok(self):

        datetime_now = self.datetime_now

        total_like_dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT / (1 - settings.BAN_AUDIO_CLIP_LIKE_RATIO)
        ban_min_age_s = 10

        #row #1

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        #pessimistic like_count to ensure ratio is as desired
        sample_audio_clip_0.like_count = math.floor(settings.BAN_AUDIO_CLIP_LIKE_RATIO * total_like_dislike_count)
        sample_audio_clip_0.dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT
        sample_audio_clip_0.like_ratio = settings.BAN_AUDIO_CLIP_LIKE_RATIO
        sample_audio_clip_0.save()
        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=ban_min_age_s)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=sample_audio_clip_0.like_ratio,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=sample_audio_clip_0.dislike_count,
                BAN_AUDIO_CLIP_MIN_AGE_S=(ban_min_age_s + 1)
            ),
            self.assertNumQueries(13)
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


    def test_cronjob_ban_audio_clips__responder_ok(self):

        datetime_now = self.datetime_now

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
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

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(13)
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


    def test_cronjob_ban_audio_clips_multiple_same_originator(self):

        #queries quantity must match singular row tests
        audio_clips_quantity = 8

        datetime_now = self.datetime_now

        total_like_dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT / (1 - settings.BAN_AUDIO_CLIP_LIKE_RATIO)
        ban_min_age_s = 10

        #rows

        sample_events = []
        sample_audio_clips = []
        sample_audio_clip_reports = []

        for x in range(audio_clips_quantity):

            sample_events.append(
                EventsFactory(
                    event_created_by=self.users[0],
                    event_generic_status_generic_status_name='incomplete',
                )
            )
            sample_audio_clips.append(
                AudioClipsFactory(
                    audio_clip_user=self.users[0],
                    audio_clip_audio_clip_role_audio_clip_role_name='originator',
                    audio_clip_event=sample_events[x],
                    audio_clip_generic_status_generic_status_name='ok',
                )
            )
            #pessimistic like_count to ensure ratio is as desired
            sample_audio_clips[x].like_count = math.floor(settings.BAN_AUDIO_CLIP_LIKE_RATIO * total_like_dislike_count)
            sample_audio_clips[x].dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT
            sample_audio_clips[x].like_ratio = settings.BAN_AUDIO_CLIP_LIKE_RATIO
            sample_audio_clips[x].save()
            #arbitrary last_evaluated, as long as < last_reported
            sample_audio_clip_reports.append(
                AudioClipReports.objects.create(
                    last_evaluated=(datetime_now - timedelta(seconds=ban_min_age_s)),
                    audio_clip_id=sample_audio_clips[x].id,
                )
            )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=settings.BAN_AUDIO_CLIP_LIKE_RATIO,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=settings.BAN_AUDIO_CLIP_DISLIKE_COUNT,
                BAN_AUDIO_CLIP_MIN_AGE_S=(ban_min_age_s + 1)
            ),
            self.assertNumQueries(13)
        ):

            cronjob_ban_audio_clips()

        #check

        self.users[0].refresh_from_db()
        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, audio_clips_quantity)

        for x in range(audio_clips_quantity):

            sample_events[x].refresh_from_db()
            sample_audio_clips[x].refresh_from_db()
            sample_audio_clip_reports[x].refresh_from_db()

            self.assertEqual(sample_events[x].generic_status.generic_status_name, 'deleted')
            self.assertEqual(sample_audio_clips[x].generic_status.generic_status_name, 'deleted')
            self.assertTrue(sample_audio_clips[x].is_banned)
            self.assertTrue(sample_audio_clip_reports[x].last_evaluated >= sample_audio_clip_reports[x].last_reported)


    def test_cronjob_ban_audio_clips_multiple_same_responder(self):

        #queries quantity must match singular row tests
        audio_clips_quantity = 8

        datetime_now = self.datetime_now

        total_like_dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT / (1 - settings.BAN_AUDIO_CLIP_LIKE_RATIO)
        ban_min_age_s = 10

        #rows

        sample_events = []
        sample_originator_audio_clips = []
        sample_responder_audio_clips = []
        sample_audio_clip_reports = []

        for x in range(audio_clips_quantity):

            sample_events.append(
                EventsFactory(
                    event_created_by=self.users[0],
                    event_generic_status_generic_status_name='incomplete',
                )
            )
            sample_originator_audio_clips.append(
                AudioClipsFactory(
                    audio_clip_user=self.users[0],
                    audio_clip_audio_clip_role_audio_clip_role_name='originator',
                    audio_clip_event=sample_events[x],
                    audio_clip_generic_status_generic_status_name='ok',
                )
            )
            sample_responder_audio_clips.append(
                AudioClipsFactory(
                    audio_clip_user=self.users[1],
                    audio_clip_audio_clip_role_audio_clip_role_name='responder',
                    audio_clip_event=sample_events[x],
                    audio_clip_generic_status_generic_status_name='ok',
                )
            )
            #pessimistic like_count to ensure ratio is as desired
            sample_responder_audio_clips[x].like_count = math.floor(settings.BAN_AUDIO_CLIP_LIKE_RATIO * total_like_dislike_count)
            sample_responder_audio_clips[x].dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT
            sample_responder_audio_clips[x].like_ratio = settings.BAN_AUDIO_CLIP_LIKE_RATIO
            sample_responder_audio_clips[x].save()
            #arbitrary last_evaluated, as long as < last_reported
            sample_audio_clip_reports.append(
                AudioClipReports.objects.create(
                    last_evaluated=(datetime_now - timedelta(seconds=ban_min_age_s)),
                    audio_clip_id=sample_responder_audio_clips[x].id,
                )
            )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=settings.BAN_AUDIO_CLIP_LIKE_RATIO,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=settings.BAN_AUDIO_CLIP_DISLIKE_COUNT,
                BAN_AUDIO_CLIP_MIN_AGE_S=(ban_min_age_s + 1)
            ),
            self.assertNumQueries(13)
        ):

            cronjob_ban_audio_clips()

        #check

        self.users[1].refresh_from_db()
        self.assertTrue(self.users[1].banned_until > datetime_now)
        self.assertEqual(self.users[1].ban_count, audio_clips_quantity)

        for x in range(audio_clips_quantity):

            sample_events[x].refresh_from_db()
            sample_responder_audio_clips[x].refresh_from_db()
            sample_audio_clip_reports[x].refresh_from_db()

            self.assertEqual(sample_events[x].generic_status.generic_status_name, 'incomplete')
            self.assertEqual(sample_responder_audio_clips[x].generic_status.generic_status_name, 'deleted')
            self.assertTrue(sample_responder_audio_clips[x].is_banned)
            self.assertTrue(sample_audio_clip_reports[x].last_evaluated >= sample_audio_clip_reports[x].last_reported)


    def test_cronjob_ban_audio_clips__same_event_all_users(self):

        datetime_now = self.datetime_now

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
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

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
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


    def test_cronjob_ban_audio_clips__different_event_different_users(self):

        datetime_now = self.datetime_now

        #event 0, ban originator

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_0.like_count = 2
        sample_audio_clip_0.dislike_count = 10
        sample_audio_clip_0.like_ratio = 0.2
        sample_audio_clip_0.save()

        #event 1, ban responder

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        sample_audio_clip_3 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_1,
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


    def test_cronjob_ban_audio_clips__different_event_same_user(self):

        datetime_now = self.datetime_now

        #event 0, ban originator

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
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

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
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


    def test_cronjob_ban_audio_clips__skip_not_reported(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
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


    def test_cronjob_ban_audio_clips__skip_already_evaluated(self):

        datetime_now = self.datetime_now

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
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


    def test_cronjob_ban_audio_clips__skip_already_banned(self):

        datetime_now = self.datetime_now

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='deleted',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
            audio_clip_is_banned=True,
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


    def test_cronjob_handle_originator_processing_overdue__ok(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0.when_created = self.datetime_now - timedelta(seconds=overdue_s)
        sample_audio_clip_0.save()

        cache_key_0 = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
            audio_clip_id=sample_audio_clip_0.id,
        )
        cache.set(cache_key_0, {})

        with self.settings(
            AUDIO_CLIP_UNPROCESSED_EXPIRY_S=(overdue_s - 1),
        ):

            cronjob_handle_originator_processing_overdue()

        self.assertFalse(Events.objects.filter(pk=sample_event_0.id).exists())
        self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_0.id).exists())
        self.assertIsNone(cache.get(cache_key_0, None))

        sample_audio_clip_0.refresh_from_db()

        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'processing_overdue')


    def test_cronjob_handle_originator_processing_overdue__multiple_ok(self):

        overdue_s = 10

        #row 1

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0.when_created = self.datetime_now - timedelta(seconds=overdue_s)
        sample_audio_clip_0.save()

        cache_key_0 = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
            audio_clip_id=sample_audio_clip_0.id,
        )
        cache.set(cache_key_0, {})

        #row 2

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_1.when_created = self.datetime_now - timedelta(seconds=overdue_s)
        sample_audio_clip_1.save()

        cache_key_1 = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
            audio_clip_id=sample_audio_clip_1.id,
        )
        cache.set(cache_key_1, {})

        with self.settings(
            AUDIO_CLIP_UNPROCESSED_EXPIRY_S=(overdue_s - 1),
        ):

            cronjob_handle_originator_processing_overdue()

        self.assertFalse(Events.objects.filter(pk=sample_event_0.id).exists())
        self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_0.id).exists())
        self.assertIsNone(cache.get(cache_key_0, None))

        self.assertFalse(Events.objects.filter(pk=sample_event_1.id).exists())
        self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_1.id).exists())
        self.assertIsNone(cache.get(cache_key_1, None))

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()

        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'processing_overdue')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'processing_overdue')


    def test_cronjob_handle_originator_processing_overdue__ignore_not_overdue(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0.when_created = self.datetime_now
        sample_audio_clip_0.save()

        cache_key_0 = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
            audio_clip_id=sample_audio_clip_0.id,
        )
        cache.set(cache_key_0, {})

        with self.settings(
            AUDIO_CLIP_UNPROCESSED_EXPIRY_S=(overdue_s - 1),
        ):

            cronjob_handle_originator_processing_overdue()

        self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
        self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_0.id).exists())
        self.assertIsNotNone(cache.get(cache_key_0, None))


    def test_cronjob_delete_event_reply_queue_not_replying_overdue__ok(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(self.datetime_now - timedelta(seconds=overdue_s))
        )

        with self.settings(
            EVENT_REPLY_CHOICE_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue_not_replying_overdue()

        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_cronjob_delete_event_reply_queue_not_replying_overdue__multiple_ok(self):

        overdue_s = 10

        #row 1

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(self.datetime_now - timedelta(seconds=overdue_s))
        )

        #row 2

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        sample_event_reply_queue_1 = self.create_event_reply_queue(
            event_id=sample_event_1.id,
            locked_for_user_id=self.users[2].id,
            is_replying=False,
            when_locked=(self.datetime_now - timedelta(seconds=overdue_s))
        )

        with self.settings(
            EVENT_REPLY_CHOICE_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue_not_replying_overdue()

        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())
        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_1.id).exists())


    def test_cronjob_delete_event_reply_queue_not_replying_overdue__ignore_not_overdue(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(self.datetime_now)
        )

        with self.settings(
            EVENT_REPLY_CHOICE_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue_not_replying_overdue()

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_cronjob_delete_event_reply_queue_not_replying_overdue__ignore_replying_expired(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(self.datetime_now - timedelta(seconds=overdue_s))
        )

        with self.settings(
            EVENT_REPLY_CHOICE_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue_not_replying_overdue()

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_cronjob_delete_event_reply_queue_is_replying_overdue__no_processing__ok(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(self.datetime_now - timedelta(seconds=overdue_s))
        )

        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue_is_replying_overdue()

        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_cronjob_delete_event_reply_queue_is_replying_overdue__no_processing__multiple_ok(self):

        overdue_s = 10

        #row 1

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(self.datetime_now - timedelta(seconds=overdue_s))
        )

        #row 2

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        sample_event_reply_queue_1 = self.create_event_reply_queue(
            event_id=sample_event_1.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(self.datetime_now - timedelta(seconds=overdue_s))
        )


        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue_is_replying_overdue()

        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())
        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_1.id).exists())


    def test_cronjob_delete_event_reply_queue_is_replying_overdue__no_processing__ignore_not_overdue(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(self.datetime_now)
        )

        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue_is_replying_overdue()

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_cronjob_delete_event_reply_queue_is_replying_overdue__no_processing__ignore_not_replying_expired(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(self.datetime_now - timedelta(seconds=overdue_s))
        )

        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue_is_replying_overdue()

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_cronjob_delete_event_reply_queue_is_replying_overdue__has_processing__ok(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(self.datetime_now - timedelta(seconds=overdue_s))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue_is_replying_overdue()

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()

        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'processing_overdue')


    def test_cronjob_delete_event_reply_queue_is_replying_overdue__has_processing__multiple_ok(self):

        overdue_s = 10

        #row 1

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(self.datetime_now - timedelta(seconds=overdue_s))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        #row 2

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        sample_event_reply_queue_1 = self.create_event_reply_queue(
            event_id=sample_event_1.id,
            locked_for_user_id=self.users[2].id,
            is_replying=True,
            when_locked=(self.datetime_now - timedelta(seconds=overdue_s))
        )

        sample_audio_clip_3 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_1,
            audio_clip_generic_status_generic_status_name='processing',
        )

        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue_is_replying_overdue()

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_2.refresh_from_db()
        sample_audio_clip_3.refresh_from_db()

        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())
        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_1.id).exists())
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'processing_overdue')
        self.assertEqual(sample_audio_clip_2.generic_status.generic_status_name, 'ok')
        self.assertEqual(sample_audio_clip_3.generic_status.generic_status_name, 'processing_overdue')


    def test_cronjob_delete_event_reply_queue_is_replying_overdue__has_processing__ignore_not_overdue(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(self.datetime_now)
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue_is_replying_overdue()

        sample_audio_clip_1.refresh_from_db()

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'processing')


    def test_cronjob_delete_audio_clip_processing_overdue__ok(self):

        audio_clips_quantity = 1

        passed_midnight_today_string = self.datetime_now.strftime('%Y-%m-%d 00:00:00.%f %z')
        passed_midnight_today = datetime.strptime(
            passed_midnight_today_string,
            '%Y-%m-%d %H:%M:%S.%f %z'
        )

        target_when_created = passed_midnight_today - timedelta(hours=24)

        #rows

        sample_originator_audio_clips = []
        sample_responder_audio_clips = []

        for x in range(audio_clips_quantity):

            sample_originator_audio_clips.append(
                AudioClipsFactory(
                    audio_clip_user=self.users[0],
                    audio_clip_audio_clip_role_audio_clip_role_name='originator',
                    audio_clip_event=None,
                    audio_clip_generic_status_generic_status_name='processing_overdue',
                )
            )
            sample_responder_audio_clips.append(
                AudioClipsFactory(
                    audio_clip_user=self.users[1],
                    audio_clip_audio_clip_role_audio_clip_role_name='responder',
                    audio_clip_event=None,
                    audio_clip_generic_status_generic_status_name='processing_overdue',
                )
            )

            sample_originator_audio_clips[x].when_created = target_when_created
            sample_originator_audio_clips[x].save()
            sample_responder_audio_clips[x].when_created = target_when_created
            sample_responder_audio_clips[x].save()

        #start

        cronjob_delete_audio_clip_processing_overdue()

        #check

        for x in range(audio_clips_quantity):

            self.assertFalse(AudioClips.objects.filter(pk=sample_originator_audio_clips[x].id).exists())
            self.assertFalse(AudioClips.objects.filter(pk=sample_responder_audio_clips[x].id).exists())


    def test_cronjob_delete_audio_clip_processing_overdue__multiple_ok(self):

        audio_clips_quantity = 1

        passed_midnight_today_string = self.datetime_now.strftime('%Y-%m-%d 00:00:00.%f %z')
        passed_midnight_today = datetime.strptime(
            passed_midnight_today_string,
            '%Y-%m-%d %H:%M:%S.%f %z'
        )

        target_when_created = passed_midnight_today - timedelta(hours=24)

        #rows

        sample_originator_audio_clips = []
        sample_responder_audio_clips = []

        for x in range(audio_clips_quantity):

            sample_originator_audio_clips.append(
                AudioClipsFactory(
                    audio_clip_user=self.users[0],
                    audio_clip_audio_clip_role_audio_clip_role_name='originator',
                    audio_clip_event=None,
                    audio_clip_generic_status_generic_status_name='processing_overdue',
                )
            )
            sample_responder_audio_clips.append(
                AudioClipsFactory(
                    audio_clip_user=self.users[1],
                    audio_clip_audio_clip_role_audio_clip_role_name='responder',
                    audio_clip_event=None,
                    audio_clip_generic_status_generic_status_name='processing_overdue',
                )
            )

            sample_originator_audio_clips[x].when_created = target_when_created
            sample_originator_audio_clips[x].save()
            sample_responder_audio_clips[x].when_created = target_when_created
            sample_responder_audio_clips[x].save()

        #start

        cronjob_delete_audio_clip_processing_overdue()

        #check

        for x in range(audio_clips_quantity):

            self.assertFalse(AudioClips.objects.filter(pk=sample_originator_audio_clips[x].id).exists())
            self.assertFalse(AudioClips.objects.filter(pk=sample_responder_audio_clips[x].id).exists())


    def test_cronjob_delete_audio_clip_processing_overdue__ignore_not_overdue(self):

        audio_clips_quantity = 1

        passed_midnight_today_string = self.datetime_now.strftime('%Y-%m-%d 00:00:00.%f %z')
        passed_midnight_today = datetime.strptime(
            passed_midnight_today_string,
            '%Y-%m-%d %H:%M:%S.%f %z'
        )

        target_when_created = self.datetime_now

        #rows

        sample_originator_audio_clips = []
        sample_responder_audio_clips = []

        for x in range(audio_clips_quantity):

            sample_originator_audio_clips.append(
                AudioClipsFactory(
                    audio_clip_user=self.users[0],
                    audio_clip_audio_clip_role_audio_clip_role_name='originator',
                    audio_clip_event=None,
                    audio_clip_generic_status_generic_status_name='deleted',
                )
            )
            sample_responder_audio_clips.append(
                AudioClipsFactory(
                    audio_clip_user=self.users[1],
                    audio_clip_audio_clip_role_audio_clip_role_name='responder',
                    audio_clip_event=None,
                    audio_clip_generic_status_generic_status_name='deleted',
                )
            )

            sample_originator_audio_clips[x].when_created = target_when_created
            sample_originator_audio_clips[x].save()
            sample_responder_audio_clips[x].when_created = target_when_created
            sample_responder_audio_clips[x].save()

        #start

        cronjob_delete_audio_clip_processing_overdue()

        #check

        for x in range(audio_clips_quantity):

            self.assertTrue(AudioClips.objects.filter(pk=sample_originator_audio_clips[x].id).exists())
            self.assertTrue(AudioClips.objects.filter(pk=sample_responder_audio_clips[x].id).exists())


    def test_cronjob_delete_audio_clip_processing_overdue__ignore_banned_audio_clips(self):

        audio_clips_quantity = 1

        passed_midnight_today_string = self.datetime_now.strftime('%Y-%m-%d 00:00:00.%f %z')
        passed_midnight_today = datetime.strptime(
            passed_midnight_today_string,
            '%Y-%m-%d %H:%M:%S.%f %z'
        )

        target_when_created = passed_midnight_today - timedelta(hours=24)

        #rows

        sample_originator_audio_clips = []
        sample_responder_audio_clips = []

        for x in range(audio_clips_quantity):

            sample_originator_audio_clips.append(
                AudioClipsFactory(
                    audio_clip_user=self.users[0],
                    audio_clip_audio_clip_role_audio_clip_role_name='originator',
                    audio_clip_event=None,
                    audio_clip_generic_status_generic_status_name='deleted',
                    audio_clip_is_banned=True,
                )
            )
            sample_responder_audio_clips.append(
                AudioClipsFactory(
                    audio_clip_user=self.users[1],
                    audio_clip_audio_clip_role_audio_clip_role_name='responder',
                    audio_clip_event=None,
                    audio_clip_generic_status_generic_status_name='deleted',
                    audio_clip_is_banned=True,
                )
            )

            sample_originator_audio_clips[x].when_created = target_when_created
            sample_originator_audio_clips[x].save()
            sample_responder_audio_clips[x].when_created = target_when_created
            sample_responder_audio_clips[x].save()

        #start

        cronjob_delete_audio_clip_processing_overdue()

        #check

        for x in range(audio_clips_quantity):

            self.assertTrue(AudioClips.objects.filter(pk=sample_originator_audio_clips[x].id).exists())
            self.assertTrue(AudioClips.objects.filter(pk=sample_responder_audio_clips[x].id).exists())

































