#Django
from time import sleep
from django.test import TestCase, Client, TransactionTestCase, override_settings
from django.urls import reverse, exceptions
from rest_framework import status
from django.core.files import File
from django.http import StreamingHttpResponse
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.db.models import Count
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, connections
from django.core.cache import cache
from celery.contrib.testing.worker import start_worker
from celery.result import AsyncResult

#py packages
import io
import json
import random
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
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
import requests
import copy
from threading import Thread

#AWS
import boto3
from botocore.exceptions import ClientError

#apps
from voicewake.services import *
from voicewake.models import *
from voicewake.tasks import *
from voicewake.factories import *
from voicewake.lambdas import *
from voicewake.apis import UserBlocksAPI, UserFollowsAPI
from voicewake.celery import app
from django.conf import settings







#multithreading only works properly with TransactionTestCase
@override_settings(
    
    DEBUG=True,
    CELERY_TASK_ALWAYS_EAGER=True,
)
class Core_TestCase(TransactionTestCase):

    @classmethod
    def setUp(cls):

        cls.datetime_now = get_datetime_now()

        #users
        cls.users = UsersFactory.create_batch(
            size=6,
        )
        cls.banned_users = UsersFactory.create_batch(
            is_banned=True,
            ban_count=1,
            size=6,
        )

        #audio file
        cls.audio_file_full_path = os.path.join(settings.BASE_DIR, 'voicewake/tests/file_samples/audio_can_overwrite.mp3')
        cls.audio_file = open(cls.audio_file_full_path, 'rb')
        cls.audio_file = SimpleUploadedFile(cls.audio_file.name, cls.audio_file.read(), 'audio/mp3')

        #bad file
        cls.bad_file_full_path = os.path.join(settings.BASE_DIR, 'voicewake/tests/file_samples/not_audio.txt')
        cls.bad_file = open(cls.bad_file_full_path, 'rb')
        cls.bad_file = SimpleUploadedFile(cls.bad_file.name, cls.bad_file.read(), 'audio/mp3')

        #get a username that is guaranteed to not exist
        cls.non_existent_username = ''

        existing_usernames = []
        
        for target_user in cls.users:

            existing_usernames.append(target_user.username)

        random_chars = ['a','b','c','d']

        for x in range(len(random_chars)):

            cls.non_existent_username += random.choice(random_chars)

        while cls.non_existent_username in existing_usernames:

            cls.non_existent_username = ''

            for x in range(len(random_chars)):

                cls.non_existent_username += random.choice(random_chars)


    @classmethod
    def tearDownClass(cls):

        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'audio_clips'), ignore_errors=True)

        try:
            cache.clear()
        except:
            pass

        super().tearDownClass()


    @classmethod
    def tearDown(cls):

        try:
            cache.clear()
        except:
            pass


    def login(self, user_instance):

        #need this here because @classmethod does not have .client attribute
        self.client.force_login(user_instance)


    def test_audio_clip_like_dislike__simultaneous_likes_from_multiple_users(self):

        #prepare 10 audio_clips

        events = []
        audio_clips = []
        audio_clip_metrics = []

        for x in range(10):

            events.append(
                EventsFactory(
                    event_created_by=self.users[0],
                    event_generic_status_generic_status_name='incomplete',
                )
            )
            audio_clips.append(
                AudioClipsFactory(
                    audio_clip_user=self.users[0],
                    audio_clip_audio_clip_role_audio_clip_role_name='originator',
                    audio_clip_event=events[x],
                    audio_clip_generic_status_generic_status_name='ok',
                )
            )
            audio_clip_metrics.append(
                AudioClipMetricsFactory(
                    audio_clip=audio_clips[x],
                )
            )

        #like function
        def do_like(login_function, user, audio_clips):

            login_function(user)

            for audio_clip in audio_clips:

                request = self.client.post(
                    reverse('audio_clip_likes_dislikes_api'),
                    data={
                        'audio_clip_id': audio_clip.id,
                        'is_liked': True,
                    }
                )

            #must close connection within each thread, else TestCase will have issue destroying database
            connections.close_all()

        threads = []

        for x in range(len(self.users)):

            threads.append(
                Thread(target=do_like, args=[self.login, self.users[x], audio_clips])
            )
            threads[x].start()

        for x in range(len(threads)):

            threads[x].join()

        #evaluate

        for audio_clip_metric in audio_clip_metrics:

            audio_clip_metric.refresh_from_db()

            self.assertEqual(audio_clip_metric.like_count, len(self.users))
            self.assertEqual(audio_clip_metric.like_ratio, 1)



