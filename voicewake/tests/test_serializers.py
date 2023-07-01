#Django
from time import sleep
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from django.core.files import File
from django.http import StreamingHttpResponse
from django.contrib.auth import get_user_model

#apps
from voicewake.services import *
from voicewake.models import *
from voicewake.serializers import *
from django.conf import settings

#py packages
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import os
import shutil
import math



class RegExp_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        pass

    def test_username_regex(self):

        good_usernames = [
            'a', '1', 'b', '2',
            'abc', 'abc123', 'a1b2c3',
            'ab.c', 'ab_c',
            'a.b.c', 'a_b_c',
            'a_b.c', 'a_b.c',
        ]

        for name in good_usernames:

            self.assertTrue(
                UsersUsernameAPISerializer(data={
                    'username': name,
                    'many': False
                }).is_valid()
            )

        bad_usernames = [
            '.a', 'a.', '.1', '1.',
            '_a', 'a_', '_1', '1_',
            'a._b', 'a_.b', 'a..b', 'a__b',
            '@', '@a', 'a@',
            'a.@b', 'a_@b1',
        ]

        for name in bad_usernames:

            self.assertFalse(
                UsersUsernameAPISerializer(data={
                    'username': name,
                    'many': False
                }).is_valid()
            )

        #found in static/json/bad_usernames.en.json
        usernames_not_allowed = [
            'admin', 'me', 'you', 'ceo'
        ]

        for name in bad_usernames:

            self.assertFalse(
                UsersUsernameAPISerializer(data={
                    'username': name,
                    'many': False
                }).is_valid()
            )



