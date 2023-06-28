#this is where you write unit testing as per Django's ways
#proper ways coming soon
#Django
from time import sleep
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from django.core.files import File
from django.http import StreamingHttpResponse
from django.contrib.auth import get_user_model
from django.core import mail

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



class Users_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.email = 'user1@gmail.com'


    def test_sign_up_correctly(self):

        #create and request OTP at the same time
        response = self.client.post(reverse('users_sign_up'), data={
            'email': self.email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.assertEqual(len(mail.outbox), 1)

        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #get OTP
        new_otp = UserOTP.objects.get(user=user_instance).otp

        #create and sign in
        response = self.client.post(reverse('users_sign_up'), data={
            'email': self.email,
            'otp': new_otp
        })

        print(response.status_code)
        print(response.data)

        #expected values
        self.assertTrue(response.data['is_logged_in'])
        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )
        self.assertTrue(user_instance.is_active)
        self.assertIsNotNone(user_instance.last_login)
        self.assertFalse(UserOTP.objects.filter(user=user_instance).exists())


    def test_log_in_for_account_that_does_not_exist(self):

        #create and request OTP at the same time
        response = self.client.post(reverse('users_log_in'), data={
            'email': self.email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.assertEqual(len(mail.outbox), 0)

        user_exists = get_user_model().objects.filter(
            email_lowercase=self.email.lower()
        ).exists()

        #user should not be created
        self.assertFalse(user_exists)

        print(response.status_code)
        print(response.data)


    def test_log_in_correctly(self):

        self.test_sign_up_correctly()

        #generate OTP
        response = self.client.post(reverse('users_log_in'), data={
            'email': self.email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.assertEqual(len(mail.outbox), 2)

        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #get correct OTP
        #should exist even after logging in from creating account,
        #because HandleUserOTP.verify_otp() deletes UserOTP row on success
        new_otp = UserOTP.objects.get(user=user_instance).otp

        #sign in
        response = self.client.post(reverse('users_log_in'), data={
            'email': self.email,
            'otp': new_otp
        })

        print(response.status_code)
        print(response.data)

        #expected values
        self.assertTrue(response.data['is_logged_in'])
        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )
        self.assertTrue(user_instance.is_active)
        self.assertIsNotNone(user_instance.last_login)
        self.assertFalse(UserOTP.objects.filter(user=user_instance).exists())





