#this is where you write unit testing as per Django's ways
#proper ways coming soon
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
from voicewake.settings import BASE_DIR

#py packages
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import os
import shutil
import math


def ensure_otp_is_always_wrong(otp):

    if int(otp[0]) == 0:
        otp = '1' + otp[1:]
    else:
        otp = str(int(otp[0]) - 1) + otp[1:]

    return otp



class UserSignIn_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        User.objects.create_user(
            email='user1@gmail.com'
        )


    def test_sign_in_process(self):

        user_instance = get_user_model().objects.get(email='user1@gmail.com')

        #generate OTP
        handle_user_otp = HandleUserOTP(
            user_instance,
            TOTP_NUMBER_OF_DIGITS, TOTP_VALIDITY_SECONDS, TOTP_TOLERANCE_SECONDS,
            OTP_CREATE_TIMEOUT_SECONDS, OTP_MAX_ATTEMPTS, OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        handle_user_otp.get_or_create_user_otp_instance()
        new_otp = handle_user_otp.generate_and_save_otp()

        self.client.post(reverse('users_sign_in'), data={
            'email': 'user1@gmail.com',
            'otp': new_otp
        })