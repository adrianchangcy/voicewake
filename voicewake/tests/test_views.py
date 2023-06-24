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
from django.conf import settings

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
        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_SECONDS, settings.TOTP_TOLERANCE_SECONDS,
            settings.OTP_CREATE_TIMEOUT_SECONDS, settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        handle_user_otp_class.get_or_create_user_otp_instance()
        new_otp = handle_user_otp_class.generate_and_save_otp()

        response = self.client.post(reverse('users_sign_in'), data={
            'email': 'user1@gmail.com',
            'otp': new_otp
        })

        print(response.status_code)
        




