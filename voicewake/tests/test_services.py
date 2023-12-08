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



class HandleUserOTP_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()
        cls.email = 'user1@gmail.com'
        User.objects.create_user(
            email=cls.email
        )
        cls.handle_user_otp_class = None


    def test_create_otp_instance_no_duplicate(self):

        user_instance = get_user_model().objects.get(email=self.email)

        self.handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, 2, 1,
            settings.OTP_CREATION_TIMEOUT_S, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )

        #create UserOTP instance
        self.handle_user_otp_class.guarantee_user_otp_instance()
        user_otp_instance = self.handle_user_otp_class.get_user_otp_instance()
        self.assertNotEqual(user_otp_instance, None)

        #attempt to create another UserOTP instance
        self.handle_user_otp_class.guarantee_user_otp_instance()
        user_otp_instance_2 = self.handle_user_otp_class.get_user_otp_instance()

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

        self.handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
            settings.OTP_CREATION_TIMEOUT_S, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )

        #create UserOTP instance
        self.handle_user_otp_class.guarantee_user_otp_instance()

        self.assertNotEqual(self.handle_user_otp_class.get_user_otp_instance(), None)
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_attempts, 0)
        self.assertEqual(self.handle_user_otp_class.get_otp_creation_timeout_seconds_left(), 0)
        self.assertEqual(self.handle_user_otp_class.get_otp_attempt_timeout_seconds_left(), 0)

        #create OTP and also save to db
        new_otp = self.handle_user_otp_class.generate_otp()
        print(new_otp)

        #expected data
        self.assertGreater(self.handle_user_otp_class.get_otp_creation_timeout_seconds_left(), 0)
        self.assertEqual(self.handle_user_otp_class.get_otp_attempt_timeout_seconds_left(), 0)

        #since we are still timed out from creating new OTP, we attempt and expect failure
        self.assertEqual(self.handle_user_otp_class.generate_otp(), '')
        self.assertGreater(self.handle_user_otp_class.get_otp_creation_timeout_seconds_left(), 0)
        self.assertEqual(self.handle_user_otp_class.get_otp_attempt_timeout_seconds_left(), 0)

        return new_otp


    def test_verify_otp_late(self):

        new_otp = self.test_create_otp()

        user_instance = get_user_model().objects.get(email=self.email)

        #notice validity and tolerance seconds being 1 here
        self.handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, 1, 1,
            settings.OTP_CREATION_TIMEOUT_S, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )

        self.handle_user_otp_class.guarantee_user_otp_instance()

        self.assertEqual(len(new_otp), settings.TOTP_NUMBER_OF_DIGITS)

        time.sleep(3)

        #verify OTP
        self.assertFalse(self.handle_user_otp_class.verify_otp(new_otp))
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_attempts, 1)


    def test_otp_creation_to_max(self):

        user_instance = get_user_model().objects.get(email=self.email)

        self.handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
            2, 2, 4,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )
        self.handle_user_otp_class.guarantee_user_otp_instance()

        #starting point
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_creations, 0)
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_last_created, None)

        #generate
        self.assertTrue(len(self.handle_user_otp_class.generate_otp()) > 0)

        #evaluate
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_creations, 1)
        self.assertNotEqual(self.handle_user_otp_class.get_user_otp_instance().otp_last_created, None)
        self.assertTrue(self.handle_user_otp_class.get_otp_creation_timeout_seconds_left() <= self.handle_user_otp_class.otp_creation_timeout_seconds)
        self.assertTrue(len(self.handle_user_otp_class.generate_otp()) == 0)

        time.sleep(self.handle_user_otp_class.otp_creation_timeout_seconds + 1)

        #generate
        self.assertTrue(len(self.handle_user_otp_class.generate_otp()) > 0)

        #evaluate
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_creations, 2)
        self.assertNotEqual(self.handle_user_otp_class.get_user_otp_instance().otp_last_created, None)
        self.assertTrue(
            self.handle_user_otp_class.get_otp_creation_timeout_seconds_left() > self.handle_user_otp_class.otp_creation_timeout_seconds and
            self.handle_user_otp_class.get_otp_creation_timeout_seconds_left() <= self.handle_user_otp_class.otp_max_creations_timeout_seconds
        )
        self.assertTrue(len(self.handle_user_otp_class.generate_otp()) == 0)

        time.sleep(self.handle_user_otp_class.otp_max_creations_timeout_seconds + 1)

        #evaluate
        self.assertTrue(self.handle_user_otp_class.get_otp_creation_timeout_seconds_left() == 0)
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_creations, 0)
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_last_created, None)

        #do success
        self.assertTrue(
            self.handle_user_otp_class.verify_otp(
                self.handle_user_otp_class.generate_otp()
            )
        )
        self.assertIsNone(self.handle_user_otp_class.get_user_otp_instance())


    def test_otp_attempt_to_max(self):

        user_instance = get_user_model().objects.get(email=self.email)

        self.handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
            2, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            2, 2
        )
        self.handle_user_otp_class.guarantee_user_otp_instance()

        #starting point
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_attempts, 0)
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_last_attempted, None)

        #get wrong otp
        otp_to_submit = ensure_otp_is_always_wrong(self.handle_user_otp_class.generate_otp())

        #verify
        self.assertFalse(self.handle_user_otp_class.verify_otp(otp_to_submit))

        #evaluate
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_attempts, 1)
        self.assertNotEqual(self.handle_user_otp_class.get_user_otp_instance().otp_last_attempted, None)

        #verify
        self.assertFalse(self.handle_user_otp_class.verify_otp(otp_to_submit))

        #evaluate, expect timeout
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_attempts, 2)
        self.assertNotEqual(self.handle_user_otp_class.get_user_otp_instance().otp_last_attempted, None)

        #not even correct otp will work
        self.assertFalse(self.handle_user_otp_class.verify_otp(self.handle_user_otp_class.otp))

        #evaluate, same state
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_attempts, 2)
        self.assertNotEqual(self.handle_user_otp_class.get_user_otp_instance().otp_last_attempted, None)
        self.assertTrue(self.handle_user_otp_class.get_otp_attempt_timeout_seconds_left() > 0)

        #sleep until timeout ends
        time.sleep(self.handle_user_otp_class.otp_max_attempts_timeout_seconds + 1)

        #evaluate
        self.assertTrue(self.handle_user_otp_class.get_otp_attempt_timeout_seconds_left() == 0)
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_attempts, 0)
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_last_attempted, None)

        #do it correctly
        #do success
        self.assertTrue(
            self.handle_user_otp_class.verify_otp(
                self.handle_user_otp_class.generate_otp()
            )
        )
        self.assertIsNone(self.handle_user_otp_class.get_user_otp_instance())


    def test_otp_creation_and_attempt(self):

        user_instance = get_user_model().objects.get(email=self.email)

        #we shorten OTP timeouts
        self.handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, 2, 2,
            1, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, 1
        )

        self.handle_user_otp_class.guarantee_user_otp_instance()
        self.handle_user_otp_class.generate_otp()

        self.assertEqual(len(self.handle_user_otp_class.otp), settings.TOTP_NUMBER_OF_DIGITS)
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_creations, 1)
        self.assertTrue(self.handle_user_otp_class.get_otp_creation_timeout_seconds_left() > 0)
        
        time.sleep(self.handle_user_otp_class.otp_creation_timeout_seconds + 1)
        self.assertFalse(self.handle_user_otp_class.get_otp_creation_timeout_seconds_left() > 0)

        #create OTP attempt that is always incorrect
        otp_to_submit = self.handle_user_otp_class.otp
        otp_to_submit = ensure_otp_is_always_wrong(otp_to_submit)

        HALF_OTP_MAX_ATTEMPTS = math.ceil(settings.OTP_MAX_ATTEMPTS / 2)

        for x in range(0, settings.OTP_MAX_ATTEMPTS):

            #when we reach about half of max attempts, we generate new OTP
            #current attempts should stay the same
            if x == HALF_OTP_MAX_ATTEMPTS:

                #wait until creating OTP is no longer timed out
                time.sleep(self.handle_user_otp_class.otp_creation_timeout_seconds + 1)
                self.assertEqual(self.handle_user_otp_class.get_otp_creation_timeout_seconds_left(), 0)

                #should be able to create new OTP, and they will not match
                current_otp = self.handle_user_otp_class.otp
                new_otp = self.handle_user_otp_class.generate_otp()

                self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_creations, 2)
                self.assertTrue(self.handle_user_otp_class.get_otp_creation_timeout_seconds_left() > 0)
                self.assertEqual(len(new_otp), settings.TOTP_NUMBER_OF_DIGITS)
                self.assertNotEqual(current_otp, new_otp)

                #update otp_to_submit to prevent the rare chance that it matches the newly generated one
                otp_to_submit = ensure_otp_is_always_wrong(new_otp)

                #attempts should stay the same after generating new OTP
                self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_attempts, x)

            #verify OTP until we reach max attempts
            #due to similar short timeouts, after waiting for new generate_otp(), verify_otp() will also trigger reset
            self.assertFalse(self.handle_user_otp_class.verify_otp(otp_to_submit))

            if x >= HALF_OTP_MAX_ATTEMPTS:
                self.assertEqual(
                    self.handle_user_otp_class.get_user_otp_instance().otp_attempts,
                    x - HALF_OTP_MAX_ATTEMPTS + 1
                )
            else:
                self.assertEqual(
                    self.handle_user_otp_class.get_user_otp_instance().otp_attempts,
                    x + 1
                )

        time.sleep(self.handle_user_otp_class.otp_max_attempts_timeout_seconds + 1)

        #otp_attempts resets on get_otp_attempt_timeout_seconds_left() call, which is in verify_otp()
        #on reset, it will still proceed with verify_otp()
        self.assertFalse(self.handle_user_otp_class.verify_otp(otp_to_submit))
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_attempts, 1)

        #push otp creation to limit
        #resume from past 2 generate_otp() calls
        for count in range(2, self.handle_user_otp_class.otp_max_creations):

            #not yet reached max creations for as long as this loop restarts
            #due to time.sleep() from previous loop
            self.assertTrue(self.handle_user_otp_class.get_otp_creation_timeout_seconds_left() <= self.handle_user_otp_class.otp_creation_timeout_seconds)
            self.assertTrue(self.handle_user_otp_class.get_otp_creation_timeout_seconds_left() < self.handle_user_otp_class.otp_max_creations_timeout_seconds)

            time.sleep(self.handle_user_otp_class.otp_creation_timeout_seconds + 1)

            self.assertTrue(len(self.handle_user_otp_class.generate_otp()) > 0)

        #should be max creation timeout now
        self.assertTrue(self.handle_user_otp_class.get_user_otp_instance().otp_creations == self.handle_user_otp_class.otp_max_creations)
        self.assertTrue(
            self.handle_user_otp_class.get_otp_creation_timeout_seconds_left() > self.handle_user_otp_class.otp_creation_timeout_seconds and
            self.handle_user_otp_class.get_otp_creation_timeout_seconds_left() <= self.handle_user_otp_class.otp_max_creations_timeout_seconds
        )
        print(self.handle_user_otp_class.get_otp_creation_timeout_seconds_left())

        #creating again should do nothing
        self.assertEqual(self.handle_user_otp_class.generate_otp(), '')

        #verify successfully
        self.assertTrue(self.handle_user_otp_class.verify_otp(self.handle_user_otp_class.otp))
        self.assertIsNone(self.handle_user_otp_class.get_user_otp_instance())


    def test_verify_otp_immediate_success(self):

        new_otp = self.test_create_otp()

        user_instance = get_user_model().objects.get(email=self.email)

        self.handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
            settings.OTP_CREATION_TIMEOUT_S, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )

        self.handle_user_otp_class.guarantee_user_otp_instance()

        #submit correct OTP
        self.assertTrue(self.handle_user_otp_class.verify_otp(new_otp))
        self.assertIsNone(self.handle_user_otp_class.get_user_otp_instance())
        self.assertFalse(
            UserOTP.objects.filter(user=user_instance).exists()
        )


    def test_verify_otp_incorrect_then_success(self):

        new_otp = self.test_create_otp()

        user_instance = get_user_model().objects.get(email=self.email)

        self.handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
            settings.OTP_CREATION_TIMEOUT_S, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )

        self.handle_user_otp_class.guarantee_user_otp_instance()

        self.assertEqual(len(new_otp), settings.TOTP_NUMBER_OF_DIGITS)

        #create OTP attempt that is always incorrect
        otp_to_submit = new_otp

        if int(otp_to_submit[0]) == 0:
            otp_to_submit = '1' + otp_to_submit[1:]
        else:
            otp_to_submit = str(int(otp_to_submit[0]) - 1) + otp_to_submit[1:]

        #two times incorrect OTP
        self.assertFalse(self.handle_user_otp_class.verify_otp(otp_to_submit))
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_attempts, 1)
        self.assertFalse(self.handle_user_otp_class.verify_otp(otp_to_submit))
        self.assertEqual(self.handle_user_otp_class.get_user_otp_instance().otp_attempts, 2)
        self.assertTrue(
            UserOTP.objects.filter(user=user_instance).exists()
        )
        #submit correct OTP
        self.assertTrue(self.handle_user_otp_class.verify_otp(new_otp))
        self.assertIsNone(self.handle_user_otp_class.get_user_otp_instance())
        self.assertFalse(
            UserOTP.objects.filter(user=user_instance).exists()
        )




