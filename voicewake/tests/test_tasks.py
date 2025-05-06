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



@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'voicewake/tests'),
    CELERY_TASK_ALWAYS_EAGER=True,
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

        #file paths
        cls.shorter_audio_file_full_path = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/audio_ok_10s.webm'
        )
        cls.longer_audio_file_full_path = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/audio_ok_120s.webm'
        )
        cls.faulty_audio_file_full_path = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/txt_as_fake_mp3.mp3'
        )


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


    def create_user_event(self, user_id:int, event_id:int, when_excluded_for_reply:datetime):

        return UserEvents.objects.create(
            user_id=user_id,
            event_id=event_id,
            when_excluded_for_reply=when_excluded_for_reply
        )


    def create_event_reply_queue(self, event_id:int, locked_for_user_id:int, is_replying:bool, when_locked:datetime):

        return EventReplyQueues.objects.create(
            event_id=event_id,
            locked_for_user_id=locked_for_user_id,
            is_replying=is_replying,
            when_locked=when_locked
        )


    def task_normalisation_expect_error(self, user_id:int, processing_cache_key:str, audio_clip_id:int, event_id:int):

        has_error = False

        try:

            task_normalisation(
                user_id=user_id,
                processing_cache_key=processing_cache_key,
                audio_clip_id=audio_clip_id,
                event_id=event_id,
            )

        except Exception as e:

            has_error = True

            print(e)

        if has_error is False:

            raise ValueError('Test passed unexpectedly.')


    def test_task_normalisation__originator__still_processing(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            created_by=self.users[0],
            generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            generic_status_name='processing',
        )

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
        target_cache['processings'][str(sample_audio_clip_0.id)]['is_processing'] = True

        cache.set(target_cache_key, target_cache)

        self.task_normalisation_expect_error(
            user_id=self.users[0].id,
            processing_cache_key=target_cache_key,
            audio_clip_id=sample_audio_clip_0.id,
            event_id=sample_event_0.id,
        )


    def test_task_normalisation__originator__failed_can_reattempt(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            created_by=self.users[0],
            generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            generic_status_name='processing',
            audio_file=self.faulty_audio_file_full_path,
        )

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

        self.task_normalisation_expect_error(
            user_id=self.users[0].id,
            processing_cache_key=target_cache_key,
            audio_clip_id=sample_audio_clip_0.id,
            event_id=sample_event_0.id,
        )


    def test_task_normalisation__originator_no_cache(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            created_by=self.users[0],
            generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            generic_status_name='processing',
        )

        #no need to create cache

        processing_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        self.task_normalisation_expect_error(
            user_id=self.users[0].id,
            processing_cache_key=processing_cache_key,
            audio_clip_id=sample_audio_clip_0.id,
            event_id=sample_event_0.id,
        )


    def test_task_normalisation__responder__still_processing(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            created_by=self.users[0],
            generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            generic_status_name='processing',
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_main_object()

        target_cache['processings'].update({
            str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_cache_processing_object(
                event=sample_audio_clip_1.event,
                audio_clip=sample_audio_clip_1,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['is_processing'] = True

        cache.set(target_cache_key, target_cache)

        #proceed

        self.task_normalisation_expect_error(
            user_id=self.users[1].id,
            processing_cache_key=target_cache_key,
            audio_clip_id=sample_audio_clip_1.id,
            event_id=sample_event_0.id,
        )


    def test_task_normalisation__responder__failed_can_reattempt(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            created_by=self.users[0],
            generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            generic_status_name='processing',
            audio_file=self.faulty_audio_file_full_path,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_main_object()

        target_cache['processings'].update({
            str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_cache_processing_object(
                event=sample_audio_clip_1.event,
                audio_clip=sample_audio_clip_1,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['is_processing'] = False

        cache.set(target_cache_key, target_cache)

        #proceed

        self.task_normalisation_expect_error(
            user_id=self.users[1].id,
            processing_cache_key=target_cache_key,
            audio_clip_id=sample_audio_clip_1.id,
            event_id=sample_event_0.id,
        )


    def test_task_normalisation__responder_no_cache(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            created_by=self.users[0],
            generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            generic_status_name='processing',
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        #no need to create cache

        processing_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        self.task_normalisation_expect_error(
            user_id=self.users[1].id,
            processing_cache_key=processing_cache_key,
            audio_clip_id=sample_audio_clip_1.id,
            event_id=sample_event_0.id,
        )


