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



class UserOTP_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        User.objects.create_user(
            username='user1',
            email='user1@gmail.com'
        )

    # def post_req_ex(self):

        # self.client.post(reverse('sign_up'), data={
        #     'username': 'listener_here',
        #     'email': 'abc@gmail.com',
        #     'password1': 'tarantula123',
        #     'password2': 'tarantula123'
        # })

    def test_first_attempt(self):

        User = get_user_model()

        #testing UserOTP
        user_instance = get_user_model().objects.get(email='user1@gmail.com')

        user_otp_object = HandleUserOTP(
            user_instance,
            TOTP_NUMBER_OF_DIGITS, TOTP_VALIDITY_SECONDS, TOTP_TOLERANCE_SECONDS,
            OTP_CREATE_TIMEOUT_SECONDS, OTP_MAX_ATTEMPTS, OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        #create UserOTP instance
        user_otp_object.create_user_otp_instance()

        self.assertNotEqual(user_otp_object.get_user_otp_instance(), None)
        self.assertEqual(user_otp_object.get_user_otp_instance().attempts, 0)
        self.assertTrue(user_otp_object.is_creating_otp_timed_out())
        self.assertFalse(user_otp_object.is_max_attempts_timed_out())

        #create OTP and also save to db
        new_otp = user_otp_object.generate_and_save_otp()

        self.assertNotEqual(user_otp_object.get_user_otp_instance().otp, '')
        print(user_otp_object.get_user_otp_instance().otp)
        self.assertNotEqual(new_otp, '')
        print(new_otp)






