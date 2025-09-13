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



def ensure_otp_is_always_wrong(otp):

    if int(otp[0]) == 0:
        otp = '1' + otp[1:]
    else:
        otp = str(int(otp[0]) - 1) + otp[1:]

    return otp



#not yet adjusted to use FactoryBoy
#BIG ISSUE
    #tests succeed individually, fail when run together
    #you will see "assertQueries(15) but only got 5", this likely means missing data in db
    #you will see "expected 'deleted' but got 'completed'/'incomplete'", this means the rows were not available, likely due to row locking elsewhere
#POTENTIAL SOLUTION
    #for any select_for_update() code, separate it into another test case class, and inherit TransactionTestCase instead
@override_settings(
    
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'voicewake/tests'),
    UNREGISTERED_USERS_MAX_INACTIVE_DURATION_S=10,
    CRONJOB_DEFAULT_ROW_LIMIT=10,
)
class Core_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.datetime_now = get_datetime_now()

        cls.users = []
        cls.inactive_user_emails = []

        for x in range(0, 6):

            current_user = get_user_model().objects.create_user(
                username='useR'+str(x),
                email='user'+str(x)+'@gmail.com',
            )

            current_user = get_user_model().objects.get(username_lowercase="user"+str(x))

            current_user.is_active = True
            current_user.save()

            cls.users.append(current_user)

            cls.inactive_user_emails.append('inactiveuser'+str(x)+'@gmail.com')

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


    def test_celery_beat_healthcheck_ok(self):

        cronjob_prepare_celery_beat_healthcheck()

        #idk why "cm" for name choice, just taking from example
        with self.assertRaises(SystemExit) as cm:

            do_celery_beat_healthcheck()

        self.assertEqual(cm.exception.code, 0)


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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        sample_audio_clip_0.when_created = self.datetime_now - timedelta(seconds=overdue_s)
        sample_audio_clip_0.save()

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_main_object()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_cache_processing_object(
                event=sample_event_0,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['is_processing'] = False

        cache.set(target_cache_key, target_cache)

        #proceed

        with self.settings(
            AUDIO_CLIP_UNPROCESSED_EXPIRY_S=(overdue_s - 1),
        ):

            cronjob_handle_originator_processing_overdue()

        self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
        self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_0.id).exists())

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertEqual(len(target_cache['processings']), 0)

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()

        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'processing_overdue')
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')


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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        sample_audio_clip_0.when_created = self.datetime_now - timedelta(seconds=overdue_s)
        sample_audio_clip_0.save()

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_main_object()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_cache_processing_object(
                event=sample_event_0,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['is_processing'] = False

        cache.set(target_cache_key, target_cache)

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
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        sample_audio_clip_1.when_created = self.datetime_now - timedelta(seconds=overdue_s)
        sample_audio_clip_1.save()

        #set cache

        target_cache['processings'].update({
            str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_cache_processing_object(
                event=sample_audio_clip_1.event,
                audio_clip=sample_audio_clip_1,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['is_processing'] = False

        cache.set(target_cache_key, target_cache)

        with self.settings(
            AUDIO_CLIP_UNPROCESSED_EXPIRY_S=(overdue_s - 1),
        ):

            cronjob_handle_originator_processing_overdue()

        self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
        self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_0.id).exists())

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertEqual(len(target_cache['processings']), 0)

        self.assertTrue(Events.objects.filter(pk=sample_event_1.id).exists())
        self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_1.id).exists())

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_event_1.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'processing_overdue')
        self.assertEqual(sample_event_1.generic_status.generic_status_name, 'deleted')
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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        sample_audio_clip_0.when_created = self.datetime_now
        sample_audio_clip_0.save()

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_main_object()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_cache_processing_object(
                event=sample_event_0,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['is_processing'] = False

        cache.set(target_cache_key, target_cache)

        with self.settings(
            AUDIO_CLIP_UNPROCESSED_EXPIRY_S=(overdue_s - 1),
        ):

            cronjob_handle_originator_processing_overdue()

        self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
        self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_0.id).exists())

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertIsNotNone(target_cache['processings'].get(str(sample_audio_clip_0.id), None))


    def test_cronjob_delete_event_reply_queue__not_replying__overdue__ok(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

            cronjob_delete_event_reply_queue__not_replying__overdue()

        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_cronjob_delete_event_reply_queue__not_replying__overdue__multiple_ok(self):

        overdue_s = 10

        #row 1

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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

            cronjob_delete_event_reply_queue__not_replying__overdue()

        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())
        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_1.id).exists())


    def test_cronjob_delete_event_reply_queue__not_replying__overdue__ignore_not_overdue(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

            cronjob_delete_event_reply_queue__not_replying__overdue()

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_cronjob_delete_event_reply_queue__not_replying__overdue__ignore_replying_expired(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

            cronjob_delete_event_reply_queue__not_replying__overdue()

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue__no_processing__ok(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

            cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue()

        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue__no_processing__multiple_ok(self):

        overdue_s = 10

        #row 1

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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

            cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue()

        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())
        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_1.id).exists())


    def test_cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue__no_processing__ignore_not_overdue(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

            cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue()

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue__no_processing__ignore_not_replying_expired(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

            cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue()

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue__has_processing__ok(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue()

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()

        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'processing_overdue')


    def test_cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue__has_processing__multiple_ok(self):

        overdue_s = 10

        #row 1

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #row 2

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )
        sample_audio_clip_metric_2 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_2,
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
        sample_audio_clip_metric_3 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_3,
        )

        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue()

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


    def test_cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue__has_processing__ignore_not_overdue(self):

        overdue_s = 10

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        with self.settings(
            EVENT_REPLY_MAX_DURATION_S=(overdue_s - 1),
        ):

            cronjob_delete_event_reply_queue__delete_audio_clip__is_replying__overdue()

        sample_audio_clip_1.refresh_from_db()

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'processing')


    def test_cronjob_delete_unregistered_users__one_ok(self):

        #sign up

        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.inactive_user_emails[0],
            'is_requesting_new_otp': True
        })

        user_instance = get_user_model().objects.get(email=self.inactive_user_emails[0])
        user_otp_instance = UserOTP.objects.get(user_id=user_instance.pk)

        #check

        self.assertIsNone(user_instance.username_lowercase)
        self.assertFalse(user_instance.is_active)
        self.assertIsNone(user_otp_instance.otp_last_attempted)

        #cronjob
        #no OTP attempt yet

        cronjob_delete_unregistered_users()

        #check

        self.assertFalse(get_user_model().objects.filter(pk=user_instance.pk).exists())
        self.assertFalse(UserOTP.objects.filter(user_id=user_instance.pk).exists())

        #new user
        #sign up

        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.inactive_user_emails[0],
            'is_requesting_new_otp': True
        })

        user_instance = get_user_model().objects.get(email=self.inactive_user_emails[0])
        user_otp_instance = UserOTP.objects.get(user_id=user_instance.pk)

        #prepare OTP

        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
            0, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )
        handle_user_otp_class.guarantee_user_otp_instance()
        new_otp = handle_user_otp_class.generate_otp()

        user_instance = get_user_model().objects.get(email=self.inactive_user_emails[0])
        user_otp_instance = UserOTP.objects.get(user_id=user_instance.pk)

        #attempt wrong OTP

        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.inactive_user_emails[0],
            'otp': ensure_otp_is_always_wrong(new_otp)
        })

        user_otp_instance.refresh_from_db()

        #prepare otp_last_attempted to qualify for deletion

        user_otp_instance.otp_last_attempted = user_otp_instance.otp_last_attempted - timedelta(seconds=settings.UNREGISTERED_USERS_MAX_INACTIVE_DURATION_S+1)
        user_otp_instance.save()
        handle_user_otp_class.user_otp_instance.refresh_from_db()

        #cronjob
        #has OTP attempt

        cronjob_delete_unregistered_users()

        #check

        self.assertFalse(get_user_model().objects.filter(pk=user_instance.pk).exists())
        self.assertFalse(UserOTP.objects.filter(user_id=user_instance.pk).exists())


    def test_cronjob_delete_unregistered_users__many_ok(self):

        all_user_ids = []

        #sign up x2, no OTP attempt

        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.inactive_user_emails[0],
            'is_requesting_new_otp': True
        })
        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.inactive_user_emails[1],
            'is_requesting_new_otp': True
        })

        all_user_ids.append(get_user_model().objects.get(email=self.inactive_user_emails[0]).pk)
        all_user_ids.append(get_user_model().objects.get(email=self.inactive_user_emails[1]).pk)

        #sign up with OTP attempt, #1

        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.inactive_user_emails[2],
            'is_requesting_new_otp': True
        })

        user_instance = get_user_model().objects.get(email=self.inactive_user_emails[2])
        user_otp_instance = UserOTP.objects.get(user_id=user_instance.pk)

        all_user_ids.append(user_instance.pk)

        #prepare OTP

        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
            0, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )
        handle_user_otp_class.guarantee_user_otp_instance()
        new_otp = handle_user_otp_class.generate_otp()

        user_instance = get_user_model().objects.get(email=self.inactive_user_emails[2])
        user_otp_instance = UserOTP.objects.get(user_id=user_instance.pk)

        #attempt wrong OTP

        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.inactive_user_emails[2],
            'otp': ensure_otp_is_always_wrong(new_otp)
        })

        user_otp_instance.refresh_from_db()

        #prepare otp_last_attempted to qualify for deletion

        user_otp_instance.otp_last_attempted = user_otp_instance.otp_last_attempted - timedelta(seconds=settings.UNREGISTERED_USERS_MAX_INACTIVE_DURATION_S+1)
        user_otp_instance.save()
        handle_user_otp_class.user_otp_instance.refresh_from_db()

        #sign up with OTP attempt, #2

        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.inactive_user_emails[3],
            'is_requesting_new_otp': True
        })

        user_instance = get_user_model().objects.get(email=self.inactive_user_emails[3])
        user_otp_instance = UserOTP.objects.get(user_id=user_instance.pk)

        all_user_ids.append(user_instance.pk)

        #prepare OTP

        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
            0, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )
        handle_user_otp_class.guarantee_user_otp_instance()
        new_otp = handle_user_otp_class.generate_otp()

        user_instance = get_user_model().objects.get(email=self.inactive_user_emails[3])
        user_otp_instance = UserOTP.objects.get(user_id=user_instance.pk)

        #attempt wrong OTP

        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.inactive_user_emails[3],
            'otp': ensure_otp_is_always_wrong(new_otp)
        })

        user_otp_instance.refresh_from_db()

        #prepare otp_last_attempted to qualify for deletion

        user_otp_instance.otp_last_attempted = user_otp_instance.otp_last_attempted - timedelta(seconds=settings.UNREGISTERED_USERS_MAX_INACTIVE_DURATION_S+1)
        user_otp_instance.save()
        handle_user_otp_class.user_otp_instance.refresh_from_db()

        #check

        self.assertEqual(get_user_model().objects.filter(is_active=False).count(), len(all_user_ids))
        self.assertEqual(UserOTP.objects.all().count(), len(all_user_ids))

        #cronjob

        cronjob_delete_unregistered_users()

        #check

        for x in all_user_ids:

            self.assertFalse(get_user_model().objects.filter(pk=x).exists())
            self.assertFalse(UserOTP.objects.filter(user_id=x).exists())


    def test_cronjob_delete_unregistered_users__no_users(self):

        #we already have pre-made "ok" users at test setup

        get_user_model().objects.all().delete()
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(UserOTP.objects.count(), 0)
        cronjob_delete_unregistered_users()


    def test_cronjob_delete_unregistered_users__no_target_users(self):

        #we already have pre-made "ok" users at test setup

        self.assertGreater(get_user_model().objects.filter(is_active=True).count(), 0)
        cronjob_delete_unregistered_users()
        self.assertEqual(get_user_model().objects.filter(is_active=False).count(), 0)
        self.assertGreater(get_user_model().objects.filter(is_active=True).count(), 0)
        self.assertEqual(UserOTP.objects.count(), 0)






@override_settings(
    
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'voicewake/tests'),
    UNREGISTERED_USERS_MAX_INACTIVE_DURATION_S=10,
)
class Core_TransactionTestCase(TransactionTestCase):

    #TransactionTestCase typically wipes entire db for better performance, in the context that you purely test transactions only
    #we are unit testing, and these tests that involve select_for_update() would mess up one another in TestCase
    #hence, this value serializes the changes, and reverses the changes after each test
    #"will slow down the test suite by approximately 3x"
    serialized_rollback = True

    #setUpTestData() does not work here, so setUp() is used
    @classmethod
    def setUp(cls):

        cls.datetime_now = get_datetime_now()

        cls.users = []
        cls.inactive_user_emails = []

        for x in range(0, 6):

            current_user = get_user_model().objects.create_user(
                username='useR'+str(x),
                email='user'+str(x)+'@gmail.com',
            )

            current_user = get_user_model().objects.get(username_lowercase="user"+str(x))

            current_user.is_active = True
            current_user.save()

            cls.users.append(current_user)

            cls.inactive_user_emails.append('inactiveuser'+str(x)+'@gmail.com')

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

        #row to be deleted

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            like_count=0,
            dislike_count=2,
            like_ratio=0,
        )

        #not delete-related row, same user

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
            like_count=2,
            dislike_count=0,
            like_ratio=1,
        )

        #like from same originator, like from someone else
        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(user=self.users[0], audio_clip=sample_audio_clip_0, is_liked=False)
        sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(user=self.users[1], audio_clip=sample_audio_clip_0, is_liked=False)

        #like that is unrelated to deleted rows
        sample_audio_clip_like_dislike_2 = AudioClipLikesDislikes.objects.create(user=self.users[0], audio_clip=sample_audio_clip_1, is_liked=True)
        sample_audio_clip_like_dislike_3 = AudioClipLikesDislikes.objects.create(user=self.users[1], audio_clip=sample_audio_clip_1, is_liked=True)

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=ban_min_age_s)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        #start

        #18 because deleting originators will always delete queues
        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=sample_audio_clip_metric_0.dislike_count,
                BAN_AUDIO_CLIP_MIN_AGE_S=(ban_min_age_s + 1)
            ),
            self.assertNumQueries(19)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, 1)
        self.assertFalse(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_0.id).exists())
        self.assertFalse(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_1.id).exists())
        self.assertTrue(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_2.id).exists())
        self.assertTrue(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_3.id).exists())


    def test_cronjob_ban_audio_clips__responder_ok(self):

        datetime_now = self.datetime_now

        #delete-related

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
            like_count=0,
            dislike_count=3,
            like_ratio=0,
        )

        #not delete-related, same users

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_2 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_2,
            like_count=1,
            dislike_count=0,
            like_ratio=1,
        )
        sample_audio_clip_3 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_3 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_3,
            like_count=2,
            dislike_count=0,
            like_ratio=1,
        )
        #like from originator, like from same responder, like from someone else
        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(user=self.users[0], audio_clip=sample_audio_clip_1, is_liked=False)
        sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(user=self.users[1], audio_clip=sample_audio_clip_1, is_liked=False)
        sample_audio_clip_like_dislike_2 = AudioClipLikesDislikes.objects.create(user=self.users[2], audio_clip=sample_audio_clip_1, is_liked=False)

        #likes on not delete-related rows
        sample_audio_clip_like_dislike_3 = AudioClipLikesDislikes.objects.create(user=self.users[0], audio_clip=sample_audio_clip_2, is_liked=True)
        sample_audio_clip_like_dislike_4 = AudioClipLikesDislikes.objects.create(user=self.users[1], audio_clip=sample_audio_clip_3, is_liked=True)
        sample_audio_clip_like_dislike_5 = AudioClipLikesDislikes.objects.create(user=self.users[2], audio_clip=sample_audio_clip_3, is_liked=True)

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_1.id,
        )

        #start

        #17 if responder has no queue
        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=3,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(18)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[1].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertTrue(self.users[1].banned_until > datetime_now)
        self.assertEqual(self.users[1].ban_count, 1)
        self.assertFalse(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_0.id).exists())
        self.assertFalse(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_1.id).exists())
        self.assertFalse(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_2.id).exists())
        self.assertTrue(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_3.id).exists())
        self.assertTrue(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_4.id).exists())
        self.assertTrue(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_5.id).exists())


    def test_cronjob_ban_audio_clips__multiple_same_originators(self):

        #queries quantity must match singular row tests
        event_quantity = 8

        datetime_now = self.datetime_now

        total_like_dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT / (1 - settings.BAN_AUDIO_CLIP_LIKE_RATIO)
        ban_min_age_s = 10

        #rows

        sample_events = []
        sample_audio_clips = []
        sample_audio_clip_metrics = []
        sample_audio_clip_reports = []

        for x in range(event_quantity):

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
            sample_audio_clip_metrics.append(
                AudioClipMetricsFactory(
                    audio_clip_metric_audio_clip=sample_audio_clips[x],
                )
            )
            #pessimistic like_count to ensure ratio is as desired
            sample_audio_clip_metrics[x].like_count = math.floor(settings.BAN_AUDIO_CLIP_LIKE_RATIO * total_like_dislike_count)
            sample_audio_clip_metrics[x].dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT
            sample_audio_clip_metrics[x].like_ratio = settings.BAN_AUDIO_CLIP_LIKE_RATIO
            sample_audio_clip_metrics[x].save()
            #arbitrary last_evaluated, as long as < last_reported
            sample_audio_clip_reports.append(
                AudioClipReports.objects.create(
                    last_evaluated=(datetime_now - timedelta(seconds=ban_min_age_s)),
                    audio_clip_id=sample_audio_clips[x].id,
                )
            )

        #start

        #set abritrary high BAN_AUDIO_CLIP_MIN_AGE_S to fix race condition between test cases
        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=settings.BAN_AUDIO_CLIP_LIKE_RATIO,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=settings.BAN_AUDIO_CLIP_DISLIKE_COUNT,
                BAN_AUDIO_CLIP_MIN_AGE_S=(ban_min_age_s + 9999)
            ),
            self.assertNumQueries(19)
        ):

            cronjob_ban_audio_clips()

        #check

        self.users[0].refresh_from_db()
        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, event_quantity)

        for x in range(event_quantity):

            sample_events[x].refresh_from_db()
            sample_audio_clips[x].refresh_from_db()
            sample_audio_clip_reports[x].refresh_from_db()
            sample_audio_clip_metrics[x].refresh_from_db()

            self.assertEqual(sample_events[x].generic_status.generic_status_name, 'deleted')
            self.assertEqual(sample_audio_clips[x].generic_status.generic_status_name, 'deleted')
            self.assertTrue(sample_audio_clips[x].is_banned)
            self.assertTrue(sample_audio_clip_reports[x].last_evaluated >= sample_audio_clip_reports[x].last_reported)
            self.assertEqual(sample_audio_clip_metrics[x].like_count, 0)
            self.assertEqual(sample_audio_clip_metrics[x].dislike_count, 0)
            self.assertEqual(sample_audio_clip_metrics[x].like_ratio, 0)


    def test_cronjob_ban_audio_clips__multiple_same_responders(self):

        #queries quantity must match singular row tests
        event_quantity = 8

        datetime_now = self.datetime_now

        total_like_dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT / (1 - settings.BAN_AUDIO_CLIP_LIKE_RATIO)
        ban_min_age_s = 10

        #rows

        sample_events = []
        sample_originator_audio_clips = []
        sample_originator_audio_clip_metrics = []
        sample_responder_audio_clips = []
        sample_responder_audio_clip_metrics = []
        sample_audio_clip_reports = []

        for x in range(event_quantity):

            sample_events.append(
                EventsFactory(
                    event_created_by=self.users[0],
                    event_generic_status_generic_status_name='completed',
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
            sample_originator_audio_clip_metrics.append(
                AudioClipMetricsFactory(
                    audio_clip_metric_audio_clip=sample_originator_audio_clips[x],
                    audio_clip_metric_like_count=math.floor(settings.BAN_AUDIO_CLIP_LIKE_RATIO * total_like_dislike_count),
                    audio_clip_metric_dislike_count=settings.BAN_AUDIO_CLIP_DISLIKE_COUNT,
                    like_ratio=settings.BAN_AUDIO_CLIP_LIKE_RATIO,
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
            sample_responder_audio_clip_metrics.append(
                AudioClipMetricsFactory(
                    audio_clip_metric_audio_clip=sample_responder_audio_clips[x],
                    audio_clip_metric_like_count=math.floor(settings.BAN_AUDIO_CLIP_LIKE_RATIO * total_like_dislike_count),
                    audio_clip_metric_dislike_count=settings.BAN_AUDIO_CLIP_DISLIKE_COUNT,
                    like_ratio=settings.BAN_AUDIO_CLIP_LIKE_RATIO,
                )
            )

            #arbitrary last_evaluated, as long as < last_reported
            sample_audio_clip_reports.append(
                AudioClipReports.objects.create(
                    last_evaluated=(datetime_now - timedelta(seconds=ban_min_age_s)),
                    audio_clip_id=sample_responder_audio_clips[x].id,
                )
            )

        #start

        #set abritrary high BAN_AUDIO_CLIP_MIN_AGE_S to fix race condition between test cases
        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=settings.BAN_AUDIO_CLIP_LIKE_RATIO,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=settings.BAN_AUDIO_CLIP_DISLIKE_COUNT,
                BAN_AUDIO_CLIP_MIN_AGE_S=(ban_min_age_s + 9999)
            ),
            self.assertNumQueries(18)
        ):

            cronjob_ban_audio_clips()

        #check

        self.users[1].refresh_from_db()
        self.assertTrue(self.users[1].banned_until > datetime_now)
        self.assertEqual(self.users[1].ban_count, event_quantity)

        for x in range(event_quantity):

            sample_events[x].refresh_from_db()
            sample_responder_audio_clips[x].refresh_from_db()
            sample_audio_clip_reports[x].refresh_from_db()
            sample_responder_audio_clip_metrics[x].refresh_from_db()

            self.assertEqual(sample_events[x].generic_status.generic_status_name, 'incomplete')
            self.assertEqual(sample_responder_audio_clips[x].generic_status.generic_status_name, 'deleted')
            self.assertTrue(sample_responder_audio_clips[x].is_banned)
            self.assertTrue(sample_audio_clip_reports[x].last_evaluated >= sample_audio_clip_reports[x].last_reported)
            self.assertEqual(sample_responder_audio_clip_metrics[x].like_count, 0)
            self.assertEqual(sample_responder_audio_clip_metrics[x].dislike_count, 0)
            self.assertEqual(sample_responder_audio_clip_metrics[x].like_ratio, 0)


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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_metric_0.like_count = 2
        sample_audio_clip_metric_0.dislike_count = 10
        sample_audio_clip_metric_0.like_ratio = 0.2
        sample_audio_clip_metric_0.save()

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        sample_audio_clip_metric_1.like_count = 2
        sample_audio_clip_metric_1.dislike_count = 10
        sample_audio_clip_metric_1.like_ratio = 0.2
        sample_audio_clip_metric_1.save()

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

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(19),
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        sample_audio_clip_report_1.refresh_from_db()
        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        sample_audio_clip_metric_0.like_count = 2
        sample_audio_clip_metric_0.dislike_count = 10
        sample_audio_clip_metric_0.like_ratio = 0.2
        sample_audio_clip_metric_0.save()

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
        sample_audio_clip_metric_2 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_2,
        )
        sample_audio_clip_3 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_1,
        )
        sample_audio_clip_metric_3 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_3,
        )
        sample_audio_clip_metric_3.like_count = 2
        sample_audio_clip_metric_3.dislike_count = 10
        sample_audio_clip_metric_3.like_ratio = 0.2
        sample_audio_clip_metric_3.save()

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

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(19),
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        sample_event_1.refresh_from_db()
        sample_audio_clip_2.refresh_from_db()
        sample_audio_clip_metric_2.refresh_from_db()
        sample_audio_clip_3.refresh_from_db()
        sample_audio_clip_metric_3.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        sample_audio_clip_report_1.refresh_from_db()
        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)

        self.assertEqual(sample_event_1.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_2.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_2.is_banned)
        self.assertEqual(sample_audio_clip_3.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_3.is_banned)
        self.assertEqual(sample_audio_clip_metric_2.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_2.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_2.like_ratio, 0)
        self.assertEqual(sample_audio_clip_metric_3.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_3.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_3.like_ratio, 0)

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_metric_0.like_count = 2
        sample_audio_clip_metric_0.dislike_count = 10
        sample_audio_clip_metric_0.like_ratio = 0.2
        sample_audio_clip_metric_0.save()

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
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        sample_audio_clip_metric_1.like_count = 2
        sample_audio_clip_metric_1.dislike_count = 10
        sample_audio_clip_metric_1.like_ratio = 0.2
        sample_audio_clip_metric_1.save()

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

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(19),
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_event_1.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        sample_audio_clip_report_1.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)

        self.assertEqual(sample_event_1.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)

        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertTrue(sample_audio_clip_report_1.last_evaluated >= sample_audio_clip_report_1.last_reported)

        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, 2)


    def test_cronjob_ban_audio_clips__deleted_audio_clip__reported(self):

        datetime_now = self.datetime_now

        total_like_dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT / (1 - settings.BAN_AUDIO_CLIP_LIKE_RATIO)
        ban_min_age_s = 10

        #row to be deleted

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='deleted',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            like_count=2,
            dislike_count=10,
            like_ratio=0.2,
        )

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=ban_min_age_s)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=sample_audio_clip_metric_0.like_ratio,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=sample_audio_clip_metric_0.dislike_count,
                BAN_AUDIO_CLIP_MIN_AGE_S=(ban_min_age_s + 1)
            ),
            self.assertNumQueries(19)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, 1)


    def test_cronjob_ban_audio_clips__deleted_audio_clip__reported_but_unqualified(self):

        datetime_now = self.datetime_now

        total_like_dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT / (1 - settings.BAN_AUDIO_CLIP_LIKE_RATIO)
        ban_min_age_s = 10

        #row to be deleted

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='deleted',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=ban_min_age_s)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        #start

        with (
            self.assertNumQueries(12)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertFalse(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertIsNone(self.users[0].banned_until)
        self.assertEqual(self.users[0].ban_count, 0)


    def test_cronjob_ban_audio_clips__A_started__B_locked_not_replying__A_banned__B_queue_removed(self):

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_event_reply_queue_0 = EventReplyQueues.objects.create(
            locked_for_user=self.users[1],
            event=sample_event_0,
            when_locked=datetime_now,
            is_replying=False,
        )

        sample_audio_clip_metric_0.like_count = 2
        sample_audio_clip_metric_0.dislike_count = 10
        sample_audio_clip_metric_0.like_ratio = 0.2
        sample_audio_clip_metric_0.save()

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(19)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, 1)
        self.assertIsNone(self.users[1].banned_until)
        self.assertEqual(self.users[1].ban_count, 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).count(), 0)


    def test_cronjob_ban_audio_clips__A_started__B_locked_is_replying__A_banned__B_queue_removed(self):

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_event_reply_queue_0 = EventReplyQueues.objects.create(
            locked_for_user=self.users[1],
            event=sample_event_0,
            when_locked=datetime_now,
            is_replying=True,
        )

        sample_audio_clip_metric_0.like_count = 2
        sample_audio_clip_metric_0.dislike_count = 10
        sample_audio_clip_metric_0.like_ratio = 0.2
        sample_audio_clip_metric_0.save()

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(19)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, 1)
        self.assertIsNone(self.users[1].banned_until)
        self.assertEqual(self.users[1].ban_count, 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).count(), 0)


    def test_cronjob_ban_audio_clips__A_started__B_locked_not_replying__A_banned__A_new_queues_removed__B_queue_removed(self):

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_event_reply_queue_0 = EventReplyQueues.objects.create(
            locked_for_user=self.users[1],
            event=sample_event_0,
            when_locked=datetime_now,
            is_replying=False,
        )

        sample_audio_clip_metric_0.like_count = 2
        sample_audio_clip_metric_0.dislike_count = 10
        sample_audio_clip_metric_0.like_ratio = 0.2
        sample_audio_clip_metric_0.save()

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        #A has new queue elsewhere

        sample_event_1 = EventsFactory(
            event_created_by=self.users[2],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )
        sample_event_reply_queue_1 = EventReplyQueues.objects.create(
            locked_for_user=self.users[0],
            event=sample_event_1,
            when_locked=datetime_now,
            is_replying=False,
        )

        #another event of A is ok, ensure everything about it is unaffected

        sample_event_2 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_2,
        )
        sample_audio_clip_metric_2 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_2,
        )
        sample_event_reply_queue_2 = EventReplyQueues.objects.create(
            locked_for_user=self.users[2],
            event=sample_event_2,
            when_locked=datetime_now,
            is_replying=False,
        )

        #extra irrelevant innocent queues

        sample_event_3 = EventsFactory(
            event_created_by=self.users[2],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_3 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_3,
        )
        sample_audio_clip_metric_3 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_3,
        )
        sample_event_reply_queue_3 = EventReplyQueues.objects.create(
            locked_for_user=self.users[3],
            event=sample_event_3,
            when_locked=datetime_now,
            is_replying=False,
        )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(19)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        sample_event_1.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        sample_event_2.refresh_from_db()
        sample_audio_clip_2.refresh_from_db()
        sample_audio_clip_metric_2.refresh_from_db()
        sample_event_3.refresh_from_db()
        sample_audio_clip_3.refresh_from_db()
        sample_audio_clip_metric_3.refresh_from_db()
        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()
        self.users[2].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertEqual(sample_event_1.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertEqual(sample_event_2.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_2.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_2.is_banned)
        self.assertEqual(sample_audio_clip_metric_3.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_3.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_3.like_ratio, 0)
        self.assertEqual(sample_event_3.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_3.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_3.is_banned)
        self.assertEqual(sample_audio_clip_metric_3.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_3.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_3.like_ratio, 0)
        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, 1)
        self.assertIsNone(self.users[1].banned_until)
        self.assertEqual(self.users[1].ban_count, 0)
        self.assertIsNone(self.users[2].banned_until)
        self.assertEqual(self.users[2].ban_count, 0)
        self.assertIsNone(self.users[3].banned_until)
        self.assertEqual(self.users[3].ban_count, 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).count(), 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_1.id).count(), 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_2.id).count(), 1)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_3.id).count(), 1)


    def test_cronjob_ban_audio_clips__A_started__B_locked_is_replying__A_banned__A_new_queues_removed__B_queue_removed(self):

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_event_reply_queue_0 = EventReplyQueues.objects.create(
            locked_for_user=self.users[1],
            event=sample_event_0,
            when_locked=datetime_now,
            is_replying=True,
        )

        sample_audio_clip_metric_0.like_count = 2
        sample_audio_clip_metric_0.dislike_count = 10
        sample_audio_clip_metric_0.like_ratio = 0.2
        sample_audio_clip_metric_0.save()

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        #A has new queue elsewhere

        sample_event_1 = EventsFactory(
            event_created_by=self.users[2],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )
        sample_event_reply_queue_1 = EventReplyQueues.objects.create(
            locked_for_user=self.users[0],
            event=sample_event_1,
            when_locked=datetime_now,
            is_replying=False,
        )

        #another event of A is ok, ensure everything about it is unaffected

        sample_event_2 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_2,
        )
        sample_audio_clip_metric_2 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_2,
        )
        sample_event_reply_queue_2 = EventReplyQueues.objects.create(
            locked_for_user=self.users[2],
            event=sample_event_2,
            when_locked=datetime_now,
            is_replying=True,
        )

        #extra irrelevant innocent queues

        sample_event_3 = EventsFactory(
            event_created_by=self.users[2],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_3 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_3,
        )
        sample_audio_clip_metric_3 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_3,
        )
        sample_event_reply_queue_3 = EventReplyQueues.objects.create(
            locked_for_user=self.users[3],
            event=sample_event_3,
            when_locked=datetime_now,
            is_replying=True,
        )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(19)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        sample_event_1.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        sample_event_2.refresh_from_db()
        sample_audio_clip_2.refresh_from_db()
        sample_audio_clip_metric_2.refresh_from_db()
        sample_event_3.refresh_from_db()
        sample_audio_clip_3.refresh_from_db()
        sample_audio_clip_metric_3.refresh_from_db()
        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()
        self.users[2].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertEqual(sample_event_1.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertEqual(sample_event_2.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_2.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_2.is_banned)
        self.assertEqual(sample_audio_clip_metric_2.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_2.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_2.like_ratio, 0)
        self.assertEqual(sample_event_3.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_3.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_3.is_banned)
        self.assertEqual(sample_audio_clip_metric_3.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_3.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_3.like_ratio, 0)
        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, 1)
        self.assertIsNone(self.users[1].banned_until)
        self.assertEqual(self.users[1].ban_count, 0)
        self.assertIsNone(self.users[2].banned_until)
        self.assertEqual(self.users[2].ban_count, 0)
        self.assertIsNone(self.users[3].banned_until)
        self.assertEqual(self.users[3].ban_count, 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).count(), 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_1.id).count(), 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_2.id).count(), 1)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_3.id).count(), 1)


    def test_cronjob_ban_audio_clips__A_started__B_replied_and_processing__A_banned__B_reply_unaffected(self):

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        sample_audio_clip_metric_0.like_count = 2
        sample_audio_clip_metric_0.dislike_count = 10
        sample_audio_clip_metric_0.like_ratio = 0.2
        sample_audio_clip_metric_0.save()

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(19)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'processing')
        self.assertFalse(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
        self.assertTrue(self.users[0].banned_until > datetime_now)
        self.assertEqual(self.users[0].ban_count, 1)
        self.assertIsNone(self.users[1].banned_until)
        self.assertEqual(self.users[1].ban_count, 0)


    def test_cronjob_ban_audio_clips__A_started__B_replied__B_new_locked_not_replying__B_banned__A_new_queues_unaffected__B_new_queues_removed(self):

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
            audio_clip_metric_like_count=2,
            audio_clip_metric_dislike_count=10,
            audio_clip_metric_like_ratio=0.2,
        )

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_1.id,
        )

        #B has new queue elsewhere

        sample_event_1 = EventsFactory(
            event_created_by=self.users[2],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )
        sample_audio_clip_metric_2 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_2,
        )
        sample_event_reply_queue_0 = EventReplyQueues.objects.create(
            locked_for_user=self.users[1],
            event=sample_event_1,
            when_locked=datetime_now,
            is_replying=False,
        )

        #another event of B is ok, ensure everything about it is unaffected

        sample_event_2 = EventsFactory(
            event_created_by=self.users[1],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_3 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_2,
        )
        sample_audio_clip_metric_3 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_3,
        )

        #new queues from A is unaffected

        sample_event_3 = EventsFactory(
            event_created_by=self.users[2],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_4 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_3,
        )
        sample_audio_clip_metric_4 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_4,
        )
        sample_event_reply_queue_1 = EventReplyQueues.objects.create(
            locked_for_user=self.users[0],
            event=sample_event_3,
            when_locked=datetime_now,
            is_replying=False,
        )

        #extra irrelevant innocent queues

        sample_event_4 = EventsFactory(
            event_created_by=self.users[2],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_5 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_4,
        )
        sample_audio_clip_metric_5 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_5,
        )
        sample_event_reply_queue_2 = EventReplyQueues.objects.create(
            locked_for_user=self.users[0],
            event=sample_event_4,
            when_locked=datetime_now,
            is_replying=False,
        )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(18)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()

        sample_event_1.refresh_from_db()
        sample_audio_clip_2.refresh_from_db()
        sample_audio_clip_metric_2.refresh_from_db()

        sample_event_2.refresh_from_db()
        sample_audio_clip_3.refresh_from_db()
        sample_audio_clip_metric_3.refresh_from_db()

        sample_event_3.refresh_from_db()
        sample_audio_clip_4.refresh_from_db()
        sample_audio_clip_metric_4.refresh_from_db()

        sample_event_4.refresh_from_db()
        sample_audio_clip_5.refresh_from_db()
        sample_audio_clip_metric_5.refresh_from_db()

        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()
        self.users[2].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)

        self.assertEqual(sample_event_1.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_2.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_2.is_banned)
        self.assertEqual(sample_audio_clip_metric_2.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_2.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_2.like_ratio, 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).count(), 0)

        self.assertEqual(sample_event_2.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_3.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_3.is_banned)
        self.assertEqual(sample_audio_clip_metric_3.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_3.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_3.like_ratio, 0)

        self.assertEqual(sample_event_3.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_4.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_4.is_banned)
        self.assertEqual(sample_audio_clip_metric_4.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_4.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_4.like_ratio, 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_1.id).count(), 1)

        self.assertEqual(sample_event_4.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_5.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_5.is_banned)
        self.assertEqual(sample_audio_clip_metric_5.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_5.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_5.like_ratio, 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_2.id).count(), 1)

        self.assertIsNone(self.users[0].banned_until)
        self.assertEqual(self.users[0].ban_count, 0)
        self.assertTrue(self.users[1].banned_until > datetime_now)
        self.assertEqual(self.users[1].ban_count, 1)
        self.assertIsNone(self.users[2].banned_until)
        self.assertEqual(self.users[2].ban_count, 0)


    def test_cronjob_ban_audio_clips__A_started__B_replied__B_new_locked_is_replying__B_banned__A_new_queues_unaffected__B_new_queues_removed(self):

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
            audio_clip_metric_like_count=2,
            audio_clip_metric_dislike_count=10,
            audio_clip_metric_like_ratio=0.2,
        )

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_1.id,
        )

        #B has new queue elsewhere

        sample_event_1 = EventsFactory(
            event_created_by=self.users[2],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )
        sample_audio_clip_metric_2 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_2,
        )
        sample_event_reply_queue_0 = EventReplyQueues.objects.create(
            locked_for_user=self.users[1],
            event=sample_event_1,
            when_locked=datetime_now,
            is_replying=True,
        )

        #another event of B is ok, ensure everything about it is unaffected

        sample_event_2 = EventsFactory(
            event_created_by=self.users[1],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_3 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_2,
        )
        sample_audio_clip_metric_3 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_3,
        )

        #new queues from A is unaffected

        sample_event_3 = EventsFactory(
            event_created_by=self.users[2],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_4 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_3,
        )
        sample_audio_clip_metric_4 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_4,
        )
        sample_event_reply_queue_1 = EventReplyQueues.objects.create(
            locked_for_user=self.users[0],
            event=sample_event_3,
            when_locked=datetime_now,
            is_replying=True,
        )

        #extra irrelevant innocent queues

        sample_event_4 = EventsFactory(
            event_created_by=self.users[2],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_5 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_4,
        )
        sample_audio_clip_metric_5 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_5,
        )
        sample_event_reply_queue_2 = EventReplyQueues.objects.create(
            locked_for_user=self.users[0],
            event=sample_event_4,
            when_locked=datetime_now,
            is_replying=True,
        )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(18)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()

        sample_event_1.refresh_from_db()
        sample_audio_clip_2.refresh_from_db()
        sample_audio_clip_metric_2.refresh_from_db()

        sample_event_2.refresh_from_db()
        sample_audio_clip_3.refresh_from_db()
        sample_audio_clip_metric_3.refresh_from_db()

        sample_event_3.refresh_from_db()
        sample_audio_clip_4.refresh_from_db()
        sample_audio_clip_metric_4.refresh_from_db()

        sample_event_4.refresh_from_db()
        sample_audio_clip_5.refresh_from_db()
        sample_audio_clip_metric_5.refresh_from_db()

        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()
        self.users[2].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)

        self.assertEqual(sample_event_1.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_2.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_2.is_banned)
        self.assertEqual(sample_audio_clip_metric_2.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_2.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_2.like_ratio, 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).count(), 0)

        self.assertEqual(sample_event_2.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_3.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_3.is_banned)
        self.assertEqual(sample_audio_clip_metric_3.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_3.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_3.like_ratio, 0)

        self.assertEqual(sample_event_3.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_4.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_4.is_banned)
        self.assertEqual(sample_audio_clip_metric_4.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_4.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_4.like_ratio, 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_1.id).count(), 1)

        self.assertEqual(sample_event_4.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_5.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_5.is_banned)
        self.assertEqual(sample_audio_clip_metric_5.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_5.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_5.like_ratio, 0)
        self.assertEqual(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_2.id).count(), 1)

        self.assertIsNone(self.users[0].banned_until)
        self.assertEqual(self.users[0].ban_count, 0)
        self.assertTrue(self.users[1].banned_until > datetime_now)
        self.assertEqual(self.users[1].ban_count, 1)
        self.assertIsNone(self.users[2].banned_until)
        self.assertEqual(self.users[2].ban_count, 0)


    def test_cronjob_ban_audio_clips__skip_qualified_but_not_reported(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            audio_clip_metric_like_count=2,
            audio_clip_metric_dislike_count=10,
            audio_clip_metric_like_ratio=0.2,
        )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(6),
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 2)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 10)
        self.assertEqual(Decimal.compare(sample_audio_clip_metric_0.like_ratio, Decimal('0.2')), Decimal('0'))
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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            audio_clip_metric_like_count=2,
            audio_clip_metric_dislike_count=10,
            audio_clip_metric_like_ratio=0.2,
        )

        #arbitrary last_evaluated, as long as > last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now + timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        previous_last_evaluated = sample_audio_clip_report_0.last_evaluated

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(6)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 2)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 10)
        self.assertEqual(Decimal.compare(sample_audio_clip_metric_0.like_ratio, Decimal('0.2')), Decimal('0'))
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
            is_banned=True,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #arbitrary last_evaluated, as long as < last_reported
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            last_evaluated=(datetime_now - timedelta(seconds=10)),
            audio_clip_id=sample_audio_clip_0.id,
        )

        previous_last_evaluated = sample_audio_clip_report_0.last_evaluated

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=0.2,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=10,
                BAN_AUDIO_CLIP_MIN_AGE_S=11,
            ),
            self.assertNumQueries(6)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(previous_last_evaluated, sample_audio_clip_report_0.last_evaluated)
        self.assertIsNone(self.users[0].banned_until)




























