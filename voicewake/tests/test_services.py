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

    def test_create_otp_instance_no_duplicate(self):

        user_instance = get_user_model().objects.get(email='user1@gmail.com')

        user_otp_object = HandleUserOTP(
            user_instance,
            TOTP_NUMBER_OF_DIGITS, 2, 1,
            OTP_CREATE_TIMEOUT_SECONDS, OTP_MAX_ATTEMPTS, OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        #create UserOTP instance
        user_otp_object.get_or_create_user_otp_instance()
        user_otp_instance = user_otp_object.get_user_otp_instance()
        self.assertNotEqual(user_otp_instance, None)

        #attempt to create another UserOTP instance
        user_otp_object.get_or_create_user_otp_instance()
        user_otp_instance_2 = user_otp_object.get_user_otp_instance()

        #should always be the same
        self.assertEqual(
            user_otp_instance,
            user_otp_instance_2
        )
        self.assertEqual(
            user_otp_instance.id,
            user_otp_instance_2.id
        )


    def test_create_otp(self):

        user_instance = get_user_model().objects.get(email='user1@gmail.com')

        user_otp_object = HandleUserOTP(
            user_instance,
            TOTP_NUMBER_OF_DIGITS, TOTP_VALIDITY_SECONDS, TOTP_TOLERANCE_SECONDS,
            OTP_CREATE_TIMEOUT_SECONDS, OTP_MAX_ATTEMPTS, OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        #create UserOTP instance
        user_otp_object.get_or_create_user_otp_instance()

        self.assertNotEqual(user_otp_object.get_user_otp_instance(), None)
        self.assertEqual(user_otp_object.get_user_otp_instance().attempts, 0)
        self.assertFalse(user_otp_object.is_creating_otp_timed_out())
        self.assertFalse(user_otp_object.is_max_attempts_timed_out())

        #create OTP and also save to db
        new_otp = user_otp_object.generate_and_save_otp()
        print(new_otp)

        #expected data
        self.assertNotEqual(user_otp_object.get_user_otp_instance().otp, '')
        self.assertTrue(user_otp_object.is_creating_otp_timed_out())
        self.assertFalse(user_otp_object.is_max_attempts_timed_out())

        #since we are still timed out from creating new OTP, we attempt and expect failure
        new_otp = user_otp_object.generate_and_save_otp()
        self.assertEqual(new_otp, '')
        self.assertNotEqual(user_otp_object.get_user_otp_instance().otp, '')
        self.assertTrue(user_otp_object.is_creating_otp_timed_out())
        self.assertFalse(user_otp_object.is_max_attempts_timed_out())

        return new_otp


    def test_verify_otp_late(self):

        new_otp = self.test_create_otp()

        user_instance = get_user_model().objects.get(email='user1@gmail.com')

        #notice validity and tolerance seconds being 1 here
        user_otp_object = HandleUserOTP(
            user_instance,
            TOTP_NUMBER_OF_DIGITS, 1, 1,
            OTP_CREATE_TIMEOUT_SECONDS, OTP_MAX_ATTEMPTS, OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        user_otp_object.get_or_create_user_otp_instance()

        self.assertEqual(len(user_otp_object.get_user_otp_instance().otp), TOTP_NUMBER_OF_DIGITS)

        time.sleep(3)

        #verify OTP
        self.assertFalse(user_otp_object.verify_otp(new_otp))
        self.assertEqual(user_otp_object.get_user_otp_instance().attempts, 1)


    def test_verify_otp_incorrect_max_attempts(self):

        self.test_create_otp()

        user_instance = get_user_model().objects.get(email='user1@gmail.com')

        user_otp_object = HandleUserOTP(
            user_instance,
            TOTP_NUMBER_OF_DIGITS, TOTP_VALIDITY_SECONDS, TOTP_TOLERANCE_SECONDS,
            OTP_CREATE_TIMEOUT_SECONDS, OTP_MAX_ATTEMPTS, OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        user_otp_object.get_or_create_user_otp_instance()

        self.assertEqual(len(user_otp_object.get_user_otp_instance().otp), TOTP_NUMBER_OF_DIGITS)

        #create OTP attempt that is always incorrect
        user_otp_submitted = user_otp_object.get_user_otp_instance().otp

        if int(user_otp_submitted[0]) == 0:
            user_otp_submitted = '1' + user_otp_submitted[1:]
        else:
            user_otp_submitted = str(int(user_otp_submitted[0]) - 1) + user_otp_submitted[1:]

        for x in range(0, OTP_MAX_ATTEMPTS):

            #verify OTP until we reach max attempts
            self.assertFalse(user_otp_object.verify_otp(user_otp_submitted))
            self.assertEqual(user_otp_object.get_user_otp_instance().attempts, x+1)

            if user_otp_object.get_user_otp_instance().attempts < OTP_MAX_ATTEMPTS:

                self.assertFalse(user_otp_object.is_max_attempts_timed_out())

            else:

                self.assertTrue(user_otp_object.is_max_attempts_timed_out())

        #while timed out, attempts shall fail
        self.assertFalse(user_otp_object.verify_otp(user_otp_submitted))
        self.assertFalse(user_otp_object.verify_otp(user_otp_object.get_user_otp_instance().otp))
        self.assertEqual(user_otp_object.get_user_otp_instance().attempts, OTP_MAX_ATTEMPTS)


    def test_verify_otp_immediate_success(self):

        self.test_create_otp()

        user_instance = get_user_model().objects.get(email='user1@gmail.com')

        user_otp_object = HandleUserOTP(
            user_instance,
            TOTP_NUMBER_OF_DIGITS, TOTP_VALIDITY_SECONDS, TOTP_TOLERANCE_SECONDS,
            OTP_CREATE_TIMEOUT_SECONDS, OTP_MAX_ATTEMPTS, OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        user_otp_object.get_or_create_user_otp_instance()

        self.assertEqual(len(user_otp_object.get_user_otp_instance().otp), TOTP_NUMBER_OF_DIGITS)

        #submit correct OTP
        self.assertTrue(user_otp_object.verify_otp(user_otp_object.get_user_otp_instance().otp))
        self.assertIsNone(user_otp_object.get_user_otp_instance())
        self.assertFalse(
            UserOTP.objects.filter(user=user_instance).exists()
        )


    def test_verify_otp_incorrect_then_success(self):

        self.test_create_otp()

        user_instance = get_user_model().objects.get(email='user1@gmail.com')

        user_otp_object = HandleUserOTP(
            user_instance,
            TOTP_NUMBER_OF_DIGITS, TOTP_VALIDITY_SECONDS, TOTP_TOLERANCE_SECONDS,
            OTP_CREATE_TIMEOUT_SECONDS, OTP_MAX_ATTEMPTS, OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        user_otp_object.get_or_create_user_otp_instance()

        self.assertEqual(len(user_otp_object.get_user_otp_instance().otp), TOTP_NUMBER_OF_DIGITS)

        #create OTP attempt that is always incorrect
        user_otp_submitted = user_otp_object.get_user_otp_instance().otp

        if int(user_otp_submitted[0]) == 0:
            user_otp_submitted = '1' + user_otp_submitted[1:]
        else:
            user_otp_submitted = str(int(user_otp_submitted[0]) - 1) + user_otp_submitted[1:]

        #two times incorrect OTP
        self.assertFalse(user_otp_object.verify_otp(user_otp_submitted))
        self.assertEqual(user_otp_object.get_user_otp_instance().attempts, 1)
        self.assertFalse(user_otp_object.verify_otp(user_otp_submitted))
        self.assertEqual(user_otp_object.get_user_otp_instance().attempts, 2)

        #submit correct OTP
        self.assertTrue(user_otp_object.verify_otp(user_otp_object.get_user_otp_instance().otp))
        self.assertIsNone(user_otp_object.get_user_otp_instance())
        self.assertFalse(
            UserOTP.objects.filter(user=user_instance).exists()
        )




