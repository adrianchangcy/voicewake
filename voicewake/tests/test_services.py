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
from voicewake.serializers import *
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



class UserOTP_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        first_time_setup()

        User = get_user_model()
        cls.email = 'user1@gmail.com'
        User.objects.create_user(
            email=cls.email
        )

    # def post_req_ex(self):

        # self.client.post(reverse('sign_up'), data={
        #     'username': 'listener_here',
        #     'email': 'abc@gmail.com',
        #     'password1': 'tarantula123',
        #     'password2': 'tarantula123'
        # })

    def test_create_otp_instance_no_duplicate(self):

        user_instance = get_user_model().objects.get(email=self.email)

        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, 2, 1,
            settings.OTP_CREATE_TIMEOUT_SECONDS, settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        #create UserOTP instance
        handle_user_otp_class.get_or_create_user_otp_instance()
        user_otp_instance = handle_user_otp_class.get_user_otp_instance()
        self.assertNotEqual(user_otp_instance, None)

        #attempt to create another UserOTP instance
        handle_user_otp_class.get_or_create_user_otp_instance()
        user_otp_instance_2 = handle_user_otp_class.get_user_otp_instance()

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

        user_instance = get_user_model().objects.get(email=self.email)

        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_SECONDS, settings.TOTP_TOLERANCE_SECONDS,
            settings.OTP_CREATE_TIMEOUT_SECONDS, settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        #create UserOTP instance
        handle_user_otp_class.get_or_create_user_otp_instance()

        self.assertNotEqual(handle_user_otp_class.get_user_otp_instance(), None)
        self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, 0)
        self.assertFalse(handle_user_otp_class.is_creating_otp_timed_out())
        self.assertFalse(handle_user_otp_class.is_max_attempts_timed_out())
        self.assertEqual(handle_user_otp_class.get_creating_otp_timed_out_seconds_left(), 0)
        self.assertEqual(handle_user_otp_class.get_max_attempts_timed_out_seconds_left(), 0)

        #create OTP and also save to db
        new_otp = handle_user_otp_class.generate_and_save_otp()
        print(new_otp)

        #expected data
        self.assertNotEqual(handle_user_otp_class.get_user_otp_instance().otp, '')
        self.assertTrue(handle_user_otp_class.is_creating_otp_timed_out())
        self.assertFalse(handle_user_otp_class.is_max_attempts_timed_out())
        self.assertGreater(handle_user_otp_class.get_creating_otp_timed_out_seconds_left(), 0)
        self.assertEqual(handle_user_otp_class.get_max_attempts_timed_out_seconds_left(), 0)

        #since we are still timed out from creating new OTP, we attempt and expect failure
        new_otp = handle_user_otp_class.generate_and_save_otp()
        self.assertEqual(new_otp, '')
        self.assertNotEqual(handle_user_otp_class.get_user_otp_instance().otp, '')
        self.assertTrue(handle_user_otp_class.is_creating_otp_timed_out())
        self.assertFalse(handle_user_otp_class.is_max_attempts_timed_out())
        self.assertGreater(handle_user_otp_class.get_creating_otp_timed_out_seconds_left(), 0)
        self.assertEqual(handle_user_otp_class.get_max_attempts_timed_out_seconds_left(), 0)

        return new_otp


    def test_verify_otp_late(self):

        new_otp = self.test_create_otp()

        user_instance = get_user_model().objects.get(email=self.email)

        #notice validity and tolerance seconds being 1 here
        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, 1, 1,
            settings.OTP_CREATE_TIMEOUT_SECONDS, settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        handle_user_otp_class.get_or_create_user_otp_instance()

        self.assertEqual(len(handle_user_otp_class.get_user_otp_instance().otp), settings.TOTP_NUMBER_OF_DIGITS)

        time.sleep(3)

        #verify OTP
        self.assertFalse(handle_user_otp_class.verify_otp(new_otp))
        self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, 1)


    def test_new_otp_maintains_attempts(self):

        user_instance = get_user_model().objects.get(email=self.email)

        #we shorten OTP timeouts
        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, 2, 2,
            1, settings.OTP_MAX_ATTEMPTS, 1
        )

        handle_user_otp_class.get_or_create_user_otp_instance()
        handle_user_otp_class.generate_and_save_otp()

        self.assertEqual(len(handle_user_otp_class.get_user_otp_instance().otp), settings.TOTP_NUMBER_OF_DIGITS)

        #create OTP attempt that is always incorrect
        otp_to_submit = handle_user_otp_class.get_user_otp_instance().otp
        otp_to_submit = ensure_otp_is_always_wrong(otp_to_submit)

        for x in range(0, settings.OTP_MAX_ATTEMPTS):

            #when we reach about half of max attempts, we generate new OTP
            #current attempts should stay the same
            if x == math.ceil(settings.OTP_MAX_ATTEMPTS / 2):

                #wait until creating OTP is no longer timed out
                time.sleep(3)
                self.assertFalse(handle_user_otp_class.is_creating_otp_timed_out())
                self.assertFalse(handle_user_otp_class.is_max_attempts_timed_out())

                #should be able to create new OTP, and they will not match
                current_otp = handle_user_otp_class.get_user_otp_instance().otp
                new_otp = handle_user_otp_class.generate_and_save_otp()
                self.assertEqual(len(new_otp), settings.TOTP_NUMBER_OF_DIGITS)
                self.assertNotEqual(current_otp, new_otp)

                #update otp_to_submit to prevent the rare chance that it matches the newly generated one
                otp_to_submit = ensure_otp_is_always_wrong(new_otp)

                #attempts should stay the same after generating new OTP
                self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, x)

            #verify OTP until we reach max attempts
            self.assertFalse(handle_user_otp_class.verify_otp(otp_to_submit))
            self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, x+1)

            if handle_user_otp_class.get_user_otp_instance().attempts < settings.OTP_MAX_ATTEMPTS:

                self.assertFalse(handle_user_otp_class.is_max_attempts_timed_out())
                self.assertEqual(handle_user_otp_class.get_max_attempts_timed_out_seconds_left(), 0)

            else:

                self.assertTrue(handle_user_otp_class.is_max_attempts_timed_out())
                self.assertGreater(handle_user_otp_class.get_max_attempts_timed_out_seconds_left(), 0)

        #while timed out, attempts shall fail
        self.assertFalse(handle_user_otp_class.verify_otp(otp_to_submit))
        self.assertFalse(handle_user_otp_class.verify_otp(handle_user_otp_class.get_user_otp_instance().otp))
        self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, settings.OTP_MAX_ATTEMPTS)

        time.sleep(3)

        #when is_max_attempts_timed_out() is called after timeout, it resets OTP and attempts in instance
        #thus, verify will fail
        self.assertFalse(handle_user_otp_class.verify_otp(otp_to_submit))
        self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, 0)
        self.assertEqual(handle_user_otp_class.get_user_otp_instance().otp, '')
        self.assertFalse(handle_user_otp_class.has_otp_saved())

        #should be able to create new OTP now
        self.assertEqual(len(handle_user_otp_class.generate_and_save_otp()), settings.TOTP_NUMBER_OF_DIGITS)
        self.assertEqual(len(handle_user_otp_class.get_user_otp_instance().otp), settings.TOTP_NUMBER_OF_DIGITS)


    def test_verify_otp_incorrect_max_attempts(self):

        user_instance = get_user_model().objects.get(email=self.email)

        #we shorten OTP timeouts
        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_SECONDS, settings.TOTP_TOLERANCE_SECONDS,
            1, settings.OTP_MAX_ATTEMPTS, 1
        )

        handle_user_otp_class.get_or_create_user_otp_instance()
        handle_user_otp_class.generate_and_save_otp()

        self.assertEqual(len(handle_user_otp_class.get_user_otp_instance().otp), settings.TOTP_NUMBER_OF_DIGITS)

        #create OTP attempt that is always incorrect
        otp_to_submit = handle_user_otp_class.get_user_otp_instance().otp
        otp_to_submit = ensure_otp_is_always_wrong(otp_to_submit)

        for x in range(0, settings.OTP_MAX_ATTEMPTS):

            #verify OTP until we reach max attempts
            self.assertFalse(handle_user_otp_class.verify_otp(otp_to_submit))
            self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, x+1)

            if handle_user_otp_class.get_user_otp_instance().attempts < settings.OTP_MAX_ATTEMPTS:

                self.assertFalse(handle_user_otp_class.is_max_attempts_timed_out())
                self.assertEqual(handle_user_otp_class.get_max_attempts_timed_out_seconds_left(), 0)

            else:

                self.assertTrue(handle_user_otp_class.is_max_attempts_timed_out())
                self.assertGreater(handle_user_otp_class.get_max_attempts_timed_out_seconds_left(), 0)

        #while timed out, attempts shall fail
        self.assertFalse(handle_user_otp_class.verify_otp(otp_to_submit))
        self.assertFalse(handle_user_otp_class.verify_otp(handle_user_otp_class.get_user_otp_instance().otp))
        self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, settings.OTP_MAX_ATTEMPTS)

        time.sleep(3)

        #when is_max_attempts_timed_out() is called after timeout, it resets OTP and attempts in instance
        self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, settings.OTP_MAX_ATTEMPTS)
        self.assertFalse(handle_user_otp_class.verify_otp(otp_to_submit))
        self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, 0)
        self.assertEqual(handle_user_otp_class.get_user_otp_instance().otp, '')
        self.assertFalse(handle_user_otp_class.has_otp_saved())

        #should be able to create new OTP now
        self.assertEqual(len(handle_user_otp_class.generate_and_save_otp()), settings.TOTP_NUMBER_OF_DIGITS)
        self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, 0)
        self.assertEqual(len(handle_user_otp_class.get_user_otp_instance().otp), settings.TOTP_NUMBER_OF_DIGITS)


    def test_verify_otp_immediate_success(self):

        self.test_create_otp()

        user_instance = get_user_model().objects.get(email=self.email)

        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_SECONDS, settings.TOTP_TOLERANCE_SECONDS,
            settings.OTP_CREATE_TIMEOUT_SECONDS, settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        handle_user_otp_class.get_or_create_user_otp_instance()

        self.assertEqual(len(handle_user_otp_class.get_user_otp_instance().otp), settings.TOTP_NUMBER_OF_DIGITS)

        #submit correct OTP
        self.assertTrue(handle_user_otp_class.verify_otp(handle_user_otp_class.get_user_otp_instance().otp))
        self.assertIsNone(handle_user_otp_class.get_user_otp_instance())
        self.assertFalse(
            UserOTP.objects.filter(user=user_instance).exists()
        )


    def test_verify_otp_incorrect_then_success(self):

        self.test_create_otp()

        user_instance = get_user_model().objects.get(email=self.email)

        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_SECONDS, settings.TOTP_TOLERANCE_SECONDS,
            settings.OTP_CREATE_TIMEOUT_SECONDS, settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
        )

        handle_user_otp_class.get_or_create_user_otp_instance()

        self.assertEqual(len(handle_user_otp_class.get_user_otp_instance().otp), settings.TOTP_NUMBER_OF_DIGITS)

        #create OTP attempt that is always incorrect
        otp_to_submit = handle_user_otp_class.get_user_otp_instance().otp

        if int(otp_to_submit[0]) == 0:
            otp_to_submit = '1' + otp_to_submit[1:]
        else:
            otp_to_submit = str(int(otp_to_submit[0]) - 1) + otp_to_submit[1:]

        #two times incorrect OTP
        self.assertFalse(handle_user_otp_class.verify_otp(otp_to_submit))
        self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, 1)
        self.assertFalse(handle_user_otp_class.verify_otp(otp_to_submit))
        self.assertEqual(handle_user_otp_class.get_user_otp_instance().attempts, 2)
        self.assertTrue(
            UserOTP.objects.filter(user=user_instance).exists()
        )
        #submit correct OTP
        self.assertTrue(handle_user_otp_class.verify_otp(handle_user_otp_class.get_user_otp_instance().otp))
        self.assertIsNone(handle_user_otp_class.get_user_otp_instance())
        self.assertFalse(
            UserOTP.objects.filter(user=user_instance).exists()
        )




