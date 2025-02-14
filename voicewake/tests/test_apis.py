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
from voicewake.celery import app
from django.conf import settings
from voicewake.cronjobs import cronjob_ban_audio_clips



#tests always auto-override DEBUG to False
#manually specify it as True via @override_settings as needed



def ensure_otp_is_always_wrong(otp):

    if int(otp[0]) == 0:
        otp = '1' + otp[1:]
    else:
        otp = str(int(otp[0]) - 1) + otp[1:]

    return otp



@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'voicewake/tests'),
    CELERY_TASK_ALWAYS_EAGER=True,
)
class Random_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

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


    @classmethod
    def tearDownClass(cls):

        pass


    def test_random(self):

        pass














@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'voicewake/tests'),
)
class AWS_TestCase(TestCase):


    @classmethod
    def setUpTestData(cls):

        #uses production bucket
        cls.upload_folder_path = 'test/'

        test_file_prefix = os.path.join(settings.BASE_DIR, 'voicewake/tests/file_samples/')

        #files for test
        cls.test_files = {
            'audio_not_mp3': {
                'file': test_file_prefix + 'audio_not_mp3.wav',
                'expected_status_code': 400,
            },
            'audio_ok_1': {
                'file': test_file_prefix + 'audio_ok_10s.webm',
                'expected_status_code': 200,
            },
            'audio_ok_2': {
                'file': test_file_prefix + 'audio_ok_120s.webm',
                'expected_status_code': 200,
            },
            'audio_too_large': {
                'file': test_file_prefix + 'audio_too_large.webm',
                'expected_status_code': 400,
            },
            'not_audio': {
                'file': test_file_prefix + 'not_audio.txt',
                'expected_status_code': 400,
            },
            'txt_as_fake_webm': {
                'file': test_file_prefix + 'txt_as_fake_webm.webm',
                'expected_status_code': 400,
            },
        }


    #test that upload works
    #this should actually be done at client-side
    def s3_post_upload(self, url, fields, local_file_path):

        with open(local_file_path, mode='rb') as object_file:

            object_file.seek(0)

            #must be 'file'
            fields['file'] = object_file.read()

            #at Python, form fields are passed as files={}
            return requests.post(
                url,
                files=fields
            )


    def test_upload_and_delete_ok(self):

        upload_key = 'test/test_upload_and_delete_ok' + '.webm'

        s3_wrapper_class = S3PostWrapper(
            is_ec2=False,
            allowed_unprocessed_file_extensions=settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=int(os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B']),
            url_expiry_s=int(os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S']),
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        upload_info = s3_wrapper_class.generate_unprocessed_presigned_post_url(upload_key)

        upload_url = upload_info['url']
        upload_fields = upload_info['fields']

        request = self.s3_post_upload(upload_url, upload_fields, self.test_files['audio_ok_1']['file'])

        print(request.request)
        print(request.headers)
        print(request.content)

        self.assertEqual(request.status_code, 204)

        #delete when done

        response = s3_wrapper_class.delete_object(upload_key)

        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 204)


    def test_upload_file_too_large(self):

        upload_key = 'test/test_upload_file_too_large' + '.webm'

        s3_wrapper_class = S3PostWrapper(
            is_ec2=False,
            allowed_unprocessed_file_extensions=settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=int(os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B']),
            url_expiry_s=int(os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S']),
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        upload_info = s3_wrapper_class.generate_unprocessed_presigned_post_url(upload_key)

        upload_url = upload_info['url']
        upload_fields = upload_info['fields']

        try:

            request = self.s3_post_upload(upload_url, upload_fields, self.test_files['audio_too_large']['file'])

            #if unexpectedly no error, delete stored file

            response = s3_wrapper_class.delete_object(upload_key)

            self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 204)

            raise ValueError('Unexpected upload success.')

        except Exception as e:

            print(e)


    def test_upload_multiple_same_file_to_same_url(self):

        upload_key = 'test/test_upload_more_files_same_url' + '.webm'

        s3_wrapper_class = S3PostWrapper(
            is_ec2=False,
            allowed_unprocessed_file_extensions=settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=int(os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B']),
            url_expiry_s=int(os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S']),
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        upload_info = s3_wrapper_class.generate_unprocessed_presigned_post_url(upload_key)

        upload_url = upload_info['url']
        upload_fields = upload_info['fields']

        request = self.s3_post_upload(upload_url, upload_fields, self.test_files['audio_ok_1']['file'])

        self.assertEqual(request.status_code, 204)

        #random sleep, and start second upload

        time.sleep(4)

        request = self.s3_post_upload(upload_url, upload_fields, self.test_files['audio_ok_1']['file'])

        print(request.status_code)
        print(request.request)
        print(request.headers)
        print(request.content)

        #delete when done

        response = s3_wrapper_class.delete_object(upload_key)

        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 204)


    def test_lambda(self):

        upload_key = 'test/test_lambda' + '.webm'

        s3_wrapper_class = S3PostWrapper(
            is_ec2=False,
            allowed_unprocessed_file_extensions=settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=int(os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B']),
            url_expiry_s=int(os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S']),
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        if s3_wrapper_class.check_object_exists(upload_key) is False:

            upload_info = s3_wrapper_class.generate_unprocessed_presigned_post_url(upload_key)

            upload_url = upload_info['url']
            upload_fields = upload_info['fields']

            request = self.s3_post_upload(upload_url, upload_fields, self.test_files['audio_ok_1']['file'])

            self.assertEqual(request.status_code, 204)

        #call lambda

        client = boto3.client(
            service_name='lambda',
            region_name=os.environ['AWS_LAMBDA_REGION_NAME'],
            aws_access_key_id=os.environ['AWS_LAMBDA_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_LAMBDA_SECRET_ACCESS_KEY'],
        )

        #at Lambda, simply retrieve in lambda_handler via event.get('keyname')
        lambda_payload = {
            'target_object_key': upload_key
        }
        lambda_payload = json.dumps(lambda_payload)
        lambda_payload = bytes(lambda_payload, encoding='utf-8')

        response = client.invoke(
            FunctionName=os.environ['AWS_LAMBDA_NORMALISE_FUNCTION_NAME'],
            InvocationType='RequestResponse',
            Payload=lambda_payload
        )

        #handle response

        #['Payload'] is StreamingBody object, so we use .read() to get bytes
        #AWS Lambda serializes entire response to JSON
        response_data = response['Payload'].read()
        response_data = bytes(response_data).decode(encoding='utf-8')
        response_data = json.loads(response_data)

        print(response_data)


    def test_production_bucket_cors_policy_rejected(self):

        pass


    def get_keys_from_ec2_in_prod(self):

        session = boto3.Session(region_name=os.environ['AWS_S3_REGION_NAME'])
        credentials = session.get_credentials()
        credentials = credentials.get_frozen_credentials()
        print(credentials.access_key)
        print(credentials.secret_key)



class AWSConnections_FromEC2_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        if settings.IS_EC2 is False:

            raise ValueError('Cannot use this test case outside of EC2.')


    def test_rds(self):

        #cannot ping RDS, so just use random query
        #https://stackoverflow.com/questions/22599172/cant-ping-aws-rds-endpoint

        print(GenericStatuses.objects.all().count())


    def test_s3(self):

        s3_wrapper_class = S3PostWrapper(
            is_ec2=settings.IS_EC2,
            allowed_unprocessed_file_extensions=settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=int(os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B']),
            url_expiry_s=int(os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S']),
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        bucket_exists = s3_wrapper_class.check_bucket_exists(
            s3_wrapper_class.unprocessed_bucket_name
        )

        self.assertEqual(bucket_exists, True)


    def test_lambda(self):

        lambda_wrapper_class = AWSLambdaWrapper(
            is_ec2=settings.IS_EC2,
            timeout_s=int(os.environ['AWS_LAMBDA_NORMALISE_TIMEOUT_S']),
            region_name=os.environ['AWS_LAMBDA_REGION_NAME'],
            aws_access_key_id=os.environ['AWS_LAMBDA_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_LAMBDA_SECRET_ACCESS_KEY'],
        )

        response = lambda_wrapper_class.invoke_normalise_audio_clips_lambda(is_ping=True)

        print(response['lambda_status_code'])


    def test_redis(self):

        #not sure if can ping ElastiCache for Redis
        #simple .get() will fail if not connected

        print(cache.get('test_key'))



@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
)
class Users_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.email = 'user1@gmail.com'
        cls.unused_email = 'abc0123456789@gmail.com'
        cls.expected_mail_outbox_count = 0


    def test_sign_up_but_missing_otp(self):

        #generate OTP
        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.expected_mail_outbox_count += 1
        self.assertEqual(len(mail.outbox), self.expected_mail_outbox_count)

        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #sign up, with recorded email
        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.email,
        })

        self.assertTrue(response.status_code, 400)

        #sign up, with unrecorded email
        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': self.unused_email,
        })

        self.assertTrue(response.status_code, 400)

        #expect
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)


    def test_sign_up_correctly(self, another_email=''):

        if len(another_email) > 0:

            email = another_email

        else:

            email = self.email

        #create and request OTP at the same time
        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.expected_mail_outbox_count += 1
        self.assertEqual(len(mail.outbox), self.expected_mail_outbox_count)

        user_instance = get_user_model().objects.get(
            email_lowercase=email.lower()
        )

        #get OTP
        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
            0, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )
        handle_user_otp_class.guarantee_user_otp_instance()
        new_otp = handle_user_otp_class.generate_otp()

        #create and log in
        response = self.client.post(reverse('users_sign_up_api'), data={
            'email': email,
            'otp': new_otp
        })

        print(response.status_code)
        print(response.data)

        #expect
        self.assertTrue(response.data['is_logged_in'])
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        user_instance = get_user_model().objects.get(
            email_lowercase=email.lower()
        )
        self.assertTrue(user_instance.is_active)
        self.assertIsNotNone(user_instance.last_login)
        self.assertFalse(UserOTP.objects.filter(user=user_instance).exists())


    def test_sign_up_log_out(self):

        self.test_sign_up_correctly()

        response = self.client.post(reverse('users_log_out_api'))

        #expect
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)


    def test_log_in_for_account_that_does_not_exist(self):

        #create and request OTP at the same time
        response = self.client.post(reverse('users_log_in_api'), data={
            'email': self.email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.assertEqual(len(mail.outbox), 1)

        user_exists = get_user_model().objects.filter(
            email_lowercase=self.email.lower()
        ).exists()

        #user should be created with only email
        self.assertTrue(user_exists)

        print(response.status_code)
        print(response.data)


    def test_log_in_but_missing_otp(self):

        self.test_sign_up_log_out()

        #generate OTP
        response = self.client.post(reverse('users_log_in_api'), data={
            'email': self.email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.expected_mail_outbox_count += 1
        self.assertEqual(len(mail.outbox), self.expected_mail_outbox_count)

        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #log in with account that exists
        response = self.client.post(reverse('users_log_in_api'), data={
            'email': self.email,
        })

        self.assertTrue(response.status_code, 400)

        #log in with account that doesn't exist
        response = self.client.post(reverse('users_log_in_api'), data={
            'email': self.unused_email,
        })

        self.assertTrue(response.status_code, 400)

        #expect
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)


    def test_log_in_correctly(self):

        self.test_sign_up_log_out()

        #generate OTP
        response = self.client.post(reverse('users_log_in_api'), data={
            'email': self.email,
            'is_requesting_new_otp': True
        })

        #has email sent
        self.expected_mail_outbox_count += 1
        self.assertEqual(len(mail.outbox), self.expected_mail_outbox_count)

        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #get correct OTP
        handle_user_otp_class = HandleUserOTP(
            user_instance,
            settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
            0, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
            settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
        )
        handle_user_otp_class.guarantee_user_otp_instance()
        new_otp = handle_user_otp_class.generate_otp()

        #log in
        response = self.client.post(reverse('users_log_in_api'), data={
            'email': self.email,
            'otp': new_otp
        })

        #expect
        self.assertEqual(response.wsgi_request.user.is_authenticated, True)
        self.assertTrue(response.data['is_logged_in'])
        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )
        self.assertTrue(user_instance.is_active)
        self.assertIsNotNone(user_instance.last_login)
        self.assertFalse(UserOTP.objects.filter(user=user_instance).exists())


    def test_log_in_log_out(self):

        #https://stackoverflow.com/a/32330839

        self.test_log_in_correctly()

        #log out
        response = self.client.post(reverse('users_log_out_api'))

        #expect
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)


    def test_set_username_not_logged_in(self):

        self.test_log_in_log_out()

        #set username
        response = self.client.post(reverse('users_set_username_api'), data={
            'username': 'user1',
        })

        #expect
        self.assertEqual(response.status_code, 403)


    def test_set_bad_username_is_logged_in(self):

        self.test_log_in_correctly()

        #set username
        response = self.client.post(reverse('users_set_username_api'), data={
            'username': 'admin',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #expect
        self.assertEqual(response.status_code, 400)
        self.assertEqual(user_instance.username, None)
        self.assertEqual(user_instance.username_lowercase, None)

        pass


    def test_set_username_is_logged_in(self):

        self.test_log_in_correctly()

        #set username
        response = self.client.post(reverse('users_set_username_api'), data={
            'username': 'user1',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #expect
        self.assertEqual(user_instance.username, 'user1')
        self.assertEqual(user_instance.username_lowercase, 'user1')


    def test_set_username_when_username_exists(self):

        self.test_set_username_is_logged_in()

        response = self.client.post(reverse('users_log_out_api'))
        self.assertEqual(response.wsgi_request.user.is_authenticated, False)

        #new account
        another_email = 'user2@gmail.com'

        self.test_sign_up_correctly(another_email)

        #set username identical to user1
        response = self.client.post(reverse('users_set_username_api'), data={
            'username': 'user1',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=another_email.lower()
        )

        #expect
        self.assertEqual(user_instance.username, None)
        self.assertEqual(user_instance.username_lowercase, None)


        #set username identical to user1, but check via case insensitive
        response = self.client.post(reverse('users_set_username_api'), data={
            'username': 'uSEr1',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=another_email.lower()
        )

        #expect
        self.assertEqual(user_instance.username, None)
        self.assertEqual(user_instance.username_lowercase, None)

        #set username, but correct
        response = self.client.post(reverse('users_set_username_api'), data={
            'username': 'user2',
        })

        user_instance = get_user_model().objects.get(
            email_lowercase=another_email.lower()
        )

        #expect
        self.assertEqual(user_instance.username, 'user2')
        self.assertEqual(user_instance.username_lowercase, 'user2')



class AudioClips_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        #example original file
        cls.source_audio_file_full_path = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/audio_ok_1.mp3'
        )

        #where to overwrite file
        cls.overwrite_audio_file_full_path = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/audio_can_overwrite.mp3'
        )

        cls.audio_file_from_recording = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/audio_ok_webm.webm'
        )


    def get_audio_file(self):

        #simulate InMemoryUploadedFile
        #if this works, then TemporaryUploadedFile() when live works too
        #since both are the same, with only 1 extra method as difference
        #can't seem to create TemporaryUploadedFile() when testing, as .read() returns b''

        #automate args
        file_extension = self.source_audio_file_full_path.split(".", -1)[-1]
        temporary_audio_file_name = 'new_recording' + '.' + file_extension
        content_type = 'audio/' + file_extension

        return InMemoryUploadedFile(
            io.FileIO(self.source_audio_file_full_path, mode="rb+"),
            'FileField',                            #to-be field if it were in form/serializer
            temporary_audio_file_name,              #doesn't have to match actual file name
            content_type,                           #Content-Type
            os.path.getsize(self.source_audio_file_full_path),  #use os.path.getsize(path) for file size, not sys.getsizeof()
            None
        )


    #only testable with ffmpeg installed
    def do_ffmpeg(self):

        #should have webm/opus and mp4/__ files for test, but too lazy for now
        #webm/opus works
        #https://dirask.com/posts/JavaScript-supported-Audio-Video-MIME-Types-by-MediaRecorder-Chrome-and-Firefox-jERn81

        # audio_file = 'audio-clips/year_2023/month_7/day_21/user_id_1/e_13.webm'

        handle_audio_file_class = AWSLambdaNormaliseAudioClips(
            is_lambda=False,
            s3_region_name=os.environ['AWS_S3_REGION_NAME'],
            s3_aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            s3_aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
            processed_file_extension=os.environ.get('AUDIO_CLIP_PROCESSED_FILE_EXTENSION', 'mp3'),
            use_timer=True,
        )

        print(handle_audio_file_class.main())



#not yet adjusted to use FactoryBoy
@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'voicewake/tests'),
    CELERY_TASK_ALWAYS_EAGER=True,
    USER_BLOCK_LIMIT=2,
    USER_FOLLOW_LIMIT=2,
)
class Core_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.datetime_now = get_datetime_now()

        #normal users
        cls.users = []

        for x in range(0, 6):

            current_user = get_user_model().objects.create_user(
                username='useR'+str(x),
                email='user'+str(x)+'@gmail.com',
            )

            current_user.is_active = True
            current_user.save()

            cls.users.append(current_user)

        cls.banned_users = []

        for x in range(0, 6):

            current_user = get_user_model().objects.create_user(
                username='bannedUseR'+str(x),
                email='bannedUser'+str(x)+'@gmail.com',
            )

            current_user.is_active = True
            current_user.ban_count = 1
            current_user.banned_until = datetime.now(timezone.utc) + relativedelta(months=1)
            current_user.save()

            cls.banned_users.append(current_user)

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


    def get_audio_file(self):

        #need this to auto-reset via seek(0)
        self.audio_file.seek(0)
        return self.audio_file


    def get_bad_file(self):

        #need this to auto-reset via seek(0)
        self.bad_file.seek(0)
        return self.bad_file


    def create_event(self, created_by, generic_status_name="incomplete"):

        return Events.objects.create(
            event_name="yolo",
            created_by=created_by,
            generic_status=GenericStatuses.objects.get(generic_status_name=generic_status_name)
        )


    def create_event_reply_queue(self, event_id:int, locked_for_user_id:int, is_replying:bool, when_locked:datetime):

        return EventReplyQueues.objects.create(
            event_id=event_id,
            locked_for_user_id=locked_for_user_id,
            is_replying=is_replying,
            when_locked=when_locked
        )


    def create_user_event(self, user_id:int, event_id:int, when_excluded_for_reply:datetime):

        return UserEvents.objects.create(
            user_id=user_id,
            event_id=event_id,
            when_excluded_for_reply=when_excluded_for_reply
        )


    def create_user_block(self, user_id:int, blocked_user_id:int):

        return UserBlocks.objects.create(
            user_id=user_id,
            blocked_user_id=blocked_user_id
        )


    #properly relies on cronjob to give us banned data
    #returns {} originator, event, audio_clip
    def prepare_banned_audio_clip_by_cronjob(
        self,
        originator_user_id:int,
        who_to_ban:Literal['originator','responder'],
        is_replying:bool,
        responder_user_id:int=None,
    ):

        if responder_user_id is None and (who_to_ban == 'responder' or is_replying is True):

            raise ValueError('responder_user_id must not be None.')

        originator = get_user_model().objects.get(pk=originator_user_id)
        responder = None

        if responder_user_id is not None:

            responder = get_user_model().objects.get(pk=responder_user_id)

        datetime_now = self.datetime_now

        total_like_dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT / (1 - settings.BAN_AUDIO_CLIP_LIKE_RATIO)
        ban_min_age_s = 10

        #prepare ban conditions

        sample_event_0 = EventsFactory(
            event_created_by=originator,
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=originator,
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_report_0 = None
        sample_audio_clip_1 = None
        sample_event_reply_queue_0 = None
        sample_user_event_0 = None

        if responder is not None:

            if is_replying is True:

                sample_event_reply_queue_0 = self.create_event_reply_queue(
                    event_id=sample_event_0.id,
                    locked_for_user_id=self.users[1].id,
                    is_replying=True,
                    when_locked=(get_datetime_now() - timedelta(seconds=0))
                )

            else:

                sample_audio_clip_1 = AudioClipsFactory(
                    audio_clip_user=self.users[1],
                    audio_clip_audio_clip_role_audio_clip_role_name='responder',
                    audio_clip_event=sample_event_0,
                )

            sample_user_event_0 = self.create_user_event(
                self.users[1].id,
                sample_event_0.id,
                when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
            )

        if who_to_ban == 'originator':

            #pessimistic like_count to ensure ratio is as desired
            sample_audio_clip_0.like_count = math.floor(settings.BAN_AUDIO_CLIP_LIKE_RATIO * total_like_dislike_count)
            sample_audio_clip_0.dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT
            sample_audio_clip_0.like_ratio = settings.BAN_AUDIO_CLIP_LIKE_RATIO
            sample_audio_clip_0.save()
            #arbitrary last_evaluated, as long as < last_reported
            sample_audio_clip_report_0 = AudioClipReports.objects.create(
                last_evaluated=(datetime_now - timedelta(seconds=ban_min_age_s)),
                audio_clip_id=sample_audio_clip_0.id,
            )

        elif who_to_ban == 'responder':

            #pessimistic like_count to ensure ratio is as desired
            sample_audio_clip_1.like_count = math.floor(settings.BAN_AUDIO_CLIP_LIKE_RATIO * total_like_dislike_count)
            sample_audio_clip_1.dislike_count = settings.BAN_AUDIO_CLIP_DISLIKE_COUNT
            sample_audio_clip_1.like_ratio = settings.BAN_AUDIO_CLIP_LIKE_RATIO
            sample_audio_clip_1.save()
            #arbitrary last_evaluated, as long as < last_reported
            sample_audio_clip_report_0 = AudioClipReports.objects.create(
                last_evaluated=(datetime_now - timedelta(seconds=ban_min_age_s)),
                audio_clip_id=sample_audio_clip_1.id,
            )

        #start

        with (
            self.settings(
                BAN_AUDIO_CLIP_LIKE_RATIO=sample_audio_clip_0.like_ratio,
                BAN_AUDIO_CLIP_DISLIKE_COUNT=sample_audio_clip_0.dislike_count,
                BAN_AUDIO_CLIP_MIN_AGE_S=(ban_min_age_s + 1)
            ),
            self.assertNumQueries(13)
        ):

            cronjob_ban_audio_clips()

        #check

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_report_0.refresh_from_db()
        originator.refresh_from_db()

        if who_to_ban == 'originator':

            self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
            self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
            self.assertTrue(sample_audio_clip_0.is_banned)
            self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
            self.assertTrue(originator.banned_until > datetime_now)
            self.assertEqual(originator.ban_count, 1)

        elif who_to_ban == 'responder':

            responder.refresh_from_db()

            self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
            self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
            self.assertFalse(sample_audio_clip_0.is_banned)
            self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
            self.assertTrue(sample_audio_clip_1.is_banned)
            self.assertTrue(sample_audio_clip_report_0.last_evaluated >= sample_audio_clip_report_0.last_reported)
            self.assertTrue(responder.banned_until > datetime_now)
            self.assertEqual(responder.ban_count, 1)

        return {
            'originator': originator,
            'responder': responder,
            'event': sample_event_0,
            'originator_audio_clip': sample_audio_clip_0,
            'responder_audio_clip': sample_audio_clip_1,
        }


    def test_create_events__upload__ok(self):

        self.login(self.users[0])

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 201)

        #check data

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('event_id' in response_data)
        self.assertTrue('audio_clip_id' in response_data)

        self.assertTrue('key' in json.loads(response_data['upload_fields']))

        self.assertEqual(Events.objects.all().count(), 1)
        self.assertEqual(AudioClips.objects.all().count(), 1)
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)

        event = Events.objects.first()
        self.assertEqual(event.generic_status.generic_status_name, 'processing')
        self.assertEqual(event.created_by_id, self.users[0].id)
        self.assertEqual(event.event_name, data['event_name'])

        audio_clip = AudioClips.objects.first()
        self.assertEqual(audio_clip.generic_status.generic_status_name, 'processing')
        self.assertEqual(audio_clip.user_id, self.users[0].id)
        self.assertEqual(audio_clip.audio_clip_tone_id, data['audio_clip_tone_id'])
        self.assertEqual(audio_clip.event.id, event.id)
        self.assertGreater(len(audio_clip.audio_file), 0)
        self.assertEqual(audio_clip.audio_duration_s, 0)
        self.assertEqual(len(audio_clip.audio_volume_peaks), 0)

        #ensure that event at this stage cannot be viewed

        request = self.client.get(
            reverse('get_events_api',
            kwargs={'event_id': audio_clip.event.id})
        )

        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(json.loads(request.content)['data']), 0)


    def test_create_events__upload__not_idempotent_ok(self):

        self.login(self.users[0])

        #first request, new records

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 201)

        #second request, new records

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 201)

        #check data

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('audio_clip_id' in response_data)

        self.assertEqual(Events.objects.all().count(), 2)
        self.assertEqual(AudioClips.objects.all().count(), 2)
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)

        events = Events.objects.all()

        for event in events:

            self.assertEqual(event.generic_status.generic_status_name, 'processing')
            self.assertEqual(event.created_by_id, self.users[0].id)
            self.assertEqual(event.event_name, data['event_name'])

            #ensure that event at this stage cannot be viewed

            request = self.client.get(
                reverse('get_events_api',
                kwargs={'event_id': event.id})
            )

            self.assertEqual(request.status_code, 200)
            self.assertEqual(len(json.loads(request.content)['data']), 0)

        audio_clips = AudioClips.objects.all()

        for audio_clip in audio_clips:

            self.assertEqual(audio_clip.generic_status.generic_status_name, 'processing')
            self.assertEqual(audio_clip.user_id, self.users[0].id)
            self.assertEqual(audio_clip.audio_clip_tone_id, data['audio_clip_tone_id'])
            self.assertGreater(len(audio_clip.audio_file), 0)
            self.assertEqual(audio_clip.audio_duration_s, 0)
            self.assertEqual(len(audio_clip.audio_volume_peaks), 0)


    def test_create_events__upload__daily_limit_reached(self):

        #time-based
        #AudioClips.GenericStatuses.generic_status_name is not relevant
        #only checks against AudioClips

        self.login(self.users[0])

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 201)

        #limit reached
        #also prove that generic_status_name is irrelevant

        with self.settings(EVENT_CREATE_DAILY_LIMIT=1):

            target_audio_clip = AudioClips.objects.first()

            #generic_status_name = 'processing'

            data={
                'event_name': 'yolo',
                'audio_clip_tone_id': 1,
                'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            }

            request = self.client.post(reverse('create_events_upload_api'), data)

            self.assertEqual(request.status_code, 400)

            #generic_status_name = 'ok'

            target_audio_clip.generic_status = GenericStatuses.objects.get(generic_status_name='ok')
            target_audio_clip.save()

            data={
                'event_name': 'yolo',
                'audio_clip_tone_id': 1,
                'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            }

            request = self.client.post(reverse('create_events_upload_api'), data)

            self.assertEqual(request.status_code, 400)

            #ensure that audio_clip that is suddenly banned still counts towards limit

            target_audio_clip.is_banned = True
            target_audio_clip.save()

            data={
                'event_name': 'yolo',
                'audio_clip_tone_id': 1,
                'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            }

            request = self.client.post(reverse('create_events_upload_api'), data)

            self.assertEqual(request.status_code, 400)

            #check

            response_data = (bytes(request.content).decode())
            response_data = json.loads(response_data)

            self.assertTrue('message' in response_data)
            self.assertTrue('event_create_daily_limit_reached' in response_data)
            self.assertTrue(response_data['event_create_daily_limit_reached'])


    def test_create_events__upload__missing_args(self):

        self.login(self.users[0])

        data={
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 400)

        data={
            'event_name': 'yolo',
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 400)

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 400)


    def test_create_events__upload__faulty_args(self):

        self.login(self.users[0])

        data={
            'event_name': '',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 400)

        data={
            'event_name': '    ',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 400)

        data={
            'event_name': 'ha   ha',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 201)

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': '1',  #fine
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 201)

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 'b',
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 400)

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': 'mp3',
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 400)


    def test_create_events__regenerate_upload_url__ok(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_audio_file = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('key' in json.loads(response_data['upload_fields']))
        self.assertFalse('event_id' in response_data)
        self.assertFalse('audio_clip_id' in response_data)


    def test_create_events__regenerate_upload_url__resubmit_ok(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_audio_file = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 200)

        #resubmit

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 200)


    def test_create_events__regenerate_upload_url__already_processed(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_audio_file = 'yolofolder/yolofile.' + os.environ['AUDIO_CLIP_PROCESSED_FILE_EXTENSION'],
            audio_clip_generic_status_generic_status_name = 'ok',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 404)


    def test_create_events__regenerate_upload_url__no_rows(self):

        self.login(self.users[0])

        #proceed

        data = {
            'audio_clip_id': 1,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 404)


    def test_create_events__regenerate_upload_url__only_own_rows_allowed(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[1],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_audio_file = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 404)


    def test_create_events__regenerate_upload_url__wrong_context_url(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_audio_file = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 200)


    def test_create_events__regenerate_upload_url__self_banned(self):

        #prepare data from cronjob

        test_data = self.prepare_banned_audio_clip_by_cronjob(
            originator_user_id=self.users[0].id,
            who_to_ban='originator',
            is_replying=False,
            responder_user_id=None,
        )

        #start

        self.login(self.users[0])

        #proceed

        data = {
            'audio_clip_id': test_data['originator_audio_clip'].id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 403)


    def test_create_events__regenerate_upload_url__missingcronjob__args(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_audio_file = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {}

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 400)


    def test_create_events__regenerate_upload_url__faulty_args(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_audio_file = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {
            'audio_clip_id': '1a',
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 400)

        data = {
            'audio_clip_id': '            ',
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 400)


    def test_create_events__process__already_processed(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_audio_file = 'yolofolder/yolofile.' + os.environ['AUDIO_CLIP_PROCESSED_FILE_EXTENSION'],
            audio_clip_generic_status_generic_status_name = 'ok',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)
        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 200)
        self.assertTrue('is_processed' in response_data)
        self.assertTrue(response_data['is_processed'])


    def test_create_events__process__still_processing(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        response_data = get_response_data(request)

        print(request.content)
        self.assertEqual(request.status_code, 409)
        self.assertTrue("is_processing" in response_data)

        self.assertTrue(response_data['is_processing'])


    def test_create_events__process__out_of_attempts(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'deleted',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing_max_attempts_reached',
        )

        #no cache

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        self.assertEqual(request.status_code, 404)


    def test_create_events__process__no_rows(self):

        self.login(self.users[0])

        #proceed

        data = {
            'audio_clip_id': 1,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 404)


    def test_create_events__process__only_own_rows_allowed(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[1],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_audio_file = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 404)


    def test_create_events__process__wrong_context_url(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_audio_file = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 200)


    def test_create_events__process__self_banned(self):

        #prepare data from cronjob

        test_data = self.prepare_banned_audio_clip_by_cronjob(
            originator_user_id=self.users[0].id,
            who_to_ban='originator',
            is_replying=False,
            responder_user_id=None,
        )

        #start

        self.login(self.users[0])

        #proceed

        data = {
            'audio_clip_id': test_data['originator_audio_clip'].id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 403)


    def test_create_events__process__missing_args(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_audio_file = 'yolofolder/yolofile.' + os.environ['AUDIO_CLIP_PROCESSED_FILE_EXTENSION'],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {}

        request = self.client.post(reverse('create_events_process_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 400)


    def test_create_events__process__faulty_args(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_audio_file = 'yolofolder/yolofile.' + os.environ['AUDIO_CLIP_PROCESSED_FILE_EXTENSION'],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {
            'audio_clip_id': 'abc',
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 400)

        data = {
            'audio_clip_id': '1a',
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 400)


    def test_get_event_ok(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertTrue('event' in response_data[0])
        self.assertTrue('originator' in response_data[0])
        self.assertTrue('responder' in response_data[0])
        self.assertFalse('event_reply_queue' in response_data[0])


    def test_get_event_has_queue__same_request_user__not_replying(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertTrue('event_reply_queue' in response_data[0])
        self.assertFalse(response_data[0]['event_reply_queue']['is_replying'])


    def test_get_event_has_queue__same_request_user__is_replying(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertTrue('event_reply_queue' in response_data[0])
        self.assertTrue(response_data[0]['event_reply_queue']['is_replying'])


    def test_get_event_has_queue__different_request_user__not_replying(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[2])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertFalse('event_reply_queue' in response_data[0])


    def test_get_event_has_queue__different_request_user__is_replying(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[2])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertFalse('event_reply_queue' in response_data[0])


    def test_get_event_has_queue__anonymous_request_user__not_replying(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertFalse('event_reply_queue' in response_data[0])


    def test_get_event_has_queue__anonymous_request_user__is_replying(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertFalse('event_reply_queue' in response_data[0])


    def test_get_event_no_audio_clips(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)


    def test_list_event_reply_choices_daily_limit_reached(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "completed"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )

        sample_event_1 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        #start

        self.login(self.users[1])

        with self.settings(EVENT_REPLY_DAILY_LIMIT=1):

            data = {}

            request = self.client.post(reverse('list_event_reply_choices_api'), data)

            print_function_name(request.content)
            self.assertEqual(request.status_code, 400)

            #check

            response_data = (bytes(request.content).decode())
            response_data = json.loads(response_data)

            self.assertFalse(
                EventReplyQueues.objects.filter(
                    locked_for_user=self.users[1], event_id=sample_event_1.id, is_replying=False
                ).exists()
            )
            self.assertTrue('message' in response_data)
            self.assertTrue('event_reply_daily_limit_reached' in response_data)
            self.assertEqual(response_data['event_reply_daily_limit_reached'], True)
            self.assertEqual(Events.objects.count(), 2)
            self.assertEqual(AudioClips.objects.count(), 3)

            #ensure that recently banned audio_clips count towards limit

            sample_audio_clip_1.is_banned = True
            sample_audio_clip_1.save()

            data = {}

            request = self.client.post(reverse('list_event_reply_choices_api'), data)

            print_function_name(request.content)
            self.assertEqual(request.status_code, 400)

            #check

            response_data = (bytes(request.content).decode())
            response_data = json.loads(response_data)

            self.assertFalse(
                EventReplyQueues.objects.filter(
                    locked_for_user=self.users[1], event_id=sample_event_1.id, is_replying=False
                ).exists()
            )
            self.assertTrue('message' in response_data)
            self.assertTrue('event_reply_daily_limit_reached' in response_data)
            self.assertEqual(response_data['event_reply_daily_limit_reached'], True)
            self.assertEqual(Events.objects.count(), 2)
            self.assertEqual(AudioClips.objects.count(), 3)


    def test_list_reply_choices_first_time_no_unlock(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check data

        response_data = get_response_data(request)
        response_data = response_data['data'][0]

        self.assertTrue('event' in response_data and type(response_data['event']) == dict)
        self.assertTrue('originator' in response_data and len(response_data['originator']) == 1)
        self.assertTrue('responder' in response_data and len(response_data['responder']) == 0)
        self.assertTrue('event_reply_queue' in response_data and type(response_data['event_reply_queue']) == dict)

        event_reply_queue = EventReplyQueues.objects.first()
        user_event = UserEvents.objects.first()

        self.assertTrue(response_data['event_reply_queue']['when_locked'] is not None)
        self.assertEqual(response_data['event_reply_queue']['is_replying'], event_reply_queue.is_replying)
        self.assertEqual(response_data['event']['id'], event_reply_queue.event_id)
        self.assertEqual(event_reply_queue.locked_for_user_id, self.users[1].id)
        self.assertEqual(UserEvents.objects.all().count(), 1)
        self.assertEqual(user_event.event_id, sample_event_0.id)
        self.assertEqual(user_event.user_id, self.users[1].id)
        self.assertIsNotNone(user_event.when_excluded_for_reply)


    def test_list_reply_choices_first_time_has_unlock(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check data

        response_data = get_response_data(request)
        response_data = response_data['data'][0]

        self.assertTrue('event' in response_data and type(response_data['event']) == dict)
        self.assertTrue('originator' in response_data and len(response_data['originator']) == 1)
        self.assertTrue('responder' in response_data and len(response_data['responder']) == 0)
        self.assertTrue('event_reply_queue' in response_data and type(response_data['event_reply_queue']) == dict)

        event_reply_queue = EventReplyQueues.objects.first()
        user_event = UserEvents.objects.first()

        self.assertTrue(response_data['event_reply_queue']['when_locked'] is not None)
        self.assertEqual(response_data['event_reply_queue']['is_replying'], event_reply_queue.is_replying)
        self.assertEqual(response_data['event']['id'], event_reply_queue.event_id)
        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertEqual(event_reply_queue.locked_for_user_id, self.users[1].id)
        self.assertEqual(UserEvents.objects.all().count(), 1)
        self.assertEqual(user_event.event_id, sample_event_0.id)
        self.assertEqual(user_event.user_id, self.users[1].id)
        self.assertIsNotNone(user_event.when_excluded_for_reply)


    def test_list_reply_choices_ensure_own_events_not_listed(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[0])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)
        response_data = response_data['data']

        self.assertEqual(response_data, [])
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(UserEvents.objects.all().count(), 0)


    def test_list_reply_choices_where_originator_is_blocked(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        user_block_0 = self.create_user_block(user_id=self.users[1].id, blocked_user_id=self.users[0].id)

        #start

        #list event

        self.login(self.users[1])

        request = self.client.post(reverse('list_event_reply_choices_api'))

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check data

        response_data = get_response_data(request)
        response_data = response_data['data']

        self.assertEqual(response_data, [])
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(UserEvents.objects.all().count(), 0)


    def test_list_reply_choices_where_responder_is_blocked(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        user_block_0 = self.create_user_block(user_id=self.users[0].id, blocked_user_id=self.users[1].id)

        #start

        #list event

        self.login(self.users[1])

        request = self.client.post(reverse('list_event_reply_choices_api'))

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check data

        response_data = get_response_data(request)
        response_data = response_data['data']

        self.assertEqual(len(response_data), 0)
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(UserEvents.objects.all().count(), 0)


    def test_list_reply_choices_where_locked_for_someone_else(self):

        self.login(self.users[2])

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #check

        request = self.client.post(reverse('list_event_reply_choices_api'))
        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        self.assertEqual(response_data['data'], [])


    def test_list_reply_choices_has_something_locked__can_return_existing_locked_rows(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #ensure when_locked does not change
        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=10))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_1 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(sample_event_0.id, response_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 1)
        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertEqual(EventReplyQueues.objects.first().id, sample_event_reply_queue_0.id)
        self.assertEqual(EventReplyQueues.objects.first().when_locked, sample_event_reply_queue_0.when_locked)


    def test_list_reply_choices_has_something_locked__skip_existing_locked_rows(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #simply ensure when_locked changes
        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=10))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_1 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        new_event_id = response_data['data'][0]['event']['id']
        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=new_event_id)

        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertEqual(UserEvents.objects.all().count(), 2)
        self.assertEqual(response_data['data'][0]['event']['id'], sample_event_1.id)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)
        self.assertNotEqual(EventReplyQueues.objects.first().when_locked, sample_event_reply_queue_0.when_locked)


    def test_list_reply_choices_has_something_locked__can_return_existing_locked_rows__has_expired(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_CHOICE_MAX_DURATION_S * 2)))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_1 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        new_event_id = response_data['data'][0]['event']['id']
        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=new_event_id)

        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertEqual(UserEvents.objects.all().count(), 2)
        self.assertEqual(new_event_id, sample_event_1.id)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)


    def test_list_reply_choices_has_something_locked__skip_existing_locked_rows__has_expired(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_CHOICE_MAX_DURATION_S * 2)))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_1 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        new_event_id = response_data['data'][0]['event']['id']
        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=new_event_id)

        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertEqual(UserEvents.objects.all().count(), 2)
        self.assertEqual(new_event_id, sample_event_1.id)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)


    def test_start_replies_ok(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_event_reply_queue_0.refresh_from_db()

        self.assertTrue(sample_event_reply_queue_0.is_replying)
        self.assertEqual(response_data['data']['event_id'], sample_event_reply_queue_0.event_id)
        self.assertEqual(
            datetime.strptime(
                response_data['data']['when_locked'], "%Y-%m-%dT%H:%M:%S.%fZ"
            ).replace(tzinfo=ZoneInfo('UTC')),
            sample_event_reply_queue_0.when_locked
        )
        self.assertEqual(
            response_data['data']['is_replying'], sample_event_reply_queue_0.is_replying
        )


    def test_start_replies_with_missing_args(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=sample_event_0.id)

        self.assertFalse(event_reply_queue.is_replying)


    def test_start_replies_with_faulty_args(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'event_id': 9999}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=sample_event_0.id)

        self.assertFalse(event_reply_queue.is_replying)


    def test_start_replies_but_never_queued(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        print_function_name(request.content)

        self.assertEqual(request.status_code, 404)


    def test_start_replies__expired(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_CHOICE_MAX_DURATION_S) * 2))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertFalse(response_data['can_retry'])
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(
            UserEvents.objects.filter(
                user=self.users[1],
                event_id=sample_event_0,
                when_excluded_for_reply__isnull=False
            ).count(),
            1
        )


    def test_start_replies__event_is_banned(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "deleted"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_generic_status_generic_status_name = 'deleted',
            audio_clip_is_banned = True,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertFalse(response_data['can_retry'])
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(
            UserEvents.objects.filter(
                user=self.users[1],
                event_id=sample_event_0,
                when_excluded_for_reply__isnull=False
            ).count(),
            1
        )


    def test_start_replies__only_own_rows_allowed(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[2].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[2].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        event_reply_queue = EventReplyQueues.objects.get(event_id=sample_event_0.id, locked_for_user=self.users[2])

        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertEqual(
            UserEvents.objects.filter(
                user=self.users[2],
                event_id=sample_event_0,
                when_excluded_for_reply__isnull=False
            ).count(),
            1
        )
        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1]).exists())
        self.assertFalse(UserEvents.objects.filter(user=self.users[1]).exists())


    def test_create_replies__upload__ok(self):

        self.login(self.users[1])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 201)

        #check

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('event_id' in response_data)
        self.assertTrue('audio_clip_id' in response_data)

        self.assertTrue('key' in json.loads(response_data['upload_fields']))

        sample_event_0.refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
        self.assertTrue(
            AudioClips.objects.filter(
                user_id=self.users[1],
                generic_status__generic_status_name='processing',
                audio_clip_role__audio_clip_role_name='responder',
                event_id=sample_event_0.id,
            ).exists()
        )
        self.assertTrue(
            EventReplyQueues.objects.filter(
                pk=sample_event_reply_queue_0.id
            ).exists()
        )


    def test_create_replies__upload__idempotent_ok(self):

        self.login(self.users[1])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #first call

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        self.assertEqual(request.status_code, 201)

        #check

        self.assertEqual(
            AudioClips.objects.filter(user=self.users[1]).count(),
            1
        )
        self.assertEqual(
            AudioClips.objects.filter(user=self.users[1]).first().audio_clip_tone_id,
            data['audio_clip_tone_id']
        )
        self.assertTrue(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )

        response_data = get_response_data(request)

        self.assertTrue('event_id' in response_data)
        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('audio_clip_id' in response_data)

        #second call
        #expected to ignore if different audio_clip_tone_id is passed

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 2,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        self.assertEqual(request.status_code, 201)

        #check

        self.assertEqual(AudioClips.objects.filter(user=self.users[1]).count(), 1)
        self.assertTrue(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )

        response_data = get_response_data(request)

        self.assertTrue('event_id' in response_data)
        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('audio_clip_id' in response_data)


    def test_create_replies__upload__already_processed(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name = 'responder',
            audio_clip_event = sample_event_0,
        )

        #proceed

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)
        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 200)
        self.assertTrue('is_processed' in response_data)
        self.assertTrue(response_data['is_processed'])


    def test_create_replies__upload__never_queued_for_it(self):

        self.login(self.users[1])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 404)


    def test_create_replies__upload__is_locked_not_replying(self):

        self.login(self.users[1])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 400)


    def test_create_replies__upload__is_locked_is_replying_is_expired(self):

        self.login(self.users[1])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_MAX_DURATION_S + 1)))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 205)

        #check

        self.assertEqual(EventReplyQueues.objects.all().count(), 0)


    def test_create_replies__upload__event_is_banned(self):

        self.login(self.users[1])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'deleted',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
            audio_clip_is_banned=True,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 404)

        #check

        self.assertEqual(EventReplyQueues.objects.all().count(), 0)


    def test_create_replies__upload__only_own_rows_allowed(self):

        self.login(self.users[1])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[2].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        self.assertEqual(request.status_code, 404)

        #now with current user having own reply

        sample_event_1 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        sample_event_reply_queue_1 = self.create_event_reply_queue(
            event_id=sample_event_1.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_1 = self.create_user_event(
            self.users[1].id,
            sample_event_1.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        self.assertEqual(request.status_code, 404)


    def test_create_replies__upload__missing_args(self):

        self.login(self.users[1])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        data = {
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        self.assertEqual(request.status_code, 400)

        data = {
            'event_id': sample_event_0.id,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        self.assertEqual(request.status_code, 400)

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        self.assertEqual(request.status_code, 400)


    def test_create_replies__upload__faulty_args(self):

        self.login(self.users[1])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        data = {
            'event_id': 9999,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        self.assertEqual(request.status_code, 404)

        data = {
            'event_id': '',
            'audio_clip_tone_id': '',
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        self.assertEqual(request.status_code, 400)

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': 'flac',
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        self.assertEqual(request.status_code, 400)


    def test_create_replies__regenerate_upload_url__ok(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('key' in json.loads(response_data['upload_fields']))
        self.assertFalse('event_id' in response_data)
        self.assertFalse('audio_clip_id' in response_data)


    def test_create_replies__regenerate_upload_url__event_banned(self):
        pass


    def test_create_replies__regenerate_upload_url__own_audio_clip_is_banned(self):
        pass


    def test_create_replies__regenerate_upload_url__resubmit_ok(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 200)

        #resubmit

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 200)


    def test_create_replies__regenerate_upload_url__already_processed(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'completed',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 404)


    def test_create_replies__regenerate_upload_url__no_rows(self):

        self.login(self.users[0])

        #proceed

        data = {
            'audio_clip_id': 1,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 404)


    def test_create_replies__regenerate_upload_url__only_own_rows_allowed(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        #other responder

        sample_event_1 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_1 = self.create_event_reply_queue(
            event_id=sample_event_1.id,
            locked_for_user_id=self.users[2].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_1 = self.create_user_event(
            self.users[2].id,
            sample_event_1.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_3 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_3.id,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 404)


    def test_create_replies__regenerate_upload_url__wrong_context_url(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 200)


    def test_create_replies__regenerate_upload_url__missing_args(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        #proceed

        data = {}

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 400)


    def test_create_replies__regenerate_upload_url__faulty_args(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        #proceed

        data = {
            'audio_clip_id': '1a',
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 400)

        data = {
            'audio_clip_id': 9999,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 404)


    def test_create_replies__process__already_processed(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'completed',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)
        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 200)
        self.assertTrue('is_processed' in response_data)
        self.assertTrue(response_data['is_processed'])


    def test_create_replies__process__still_processing(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 409)
        self.assertTrue("is_processing" in response_data)
        self.assertTrue("attempts_left" in response_data)

        self.assertTrue(response_data['is_processing'])
        self.assertEqual(
            response_data['attempts_left'],
            settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        )
        self.assertTrue(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )


    def test_create_replies__process__out_of_attempts(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing_max_attempts_reached',
        )

        #no cache

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        self.assertEqual(request.status_code, 404)


    def test_create_replies__process__event_is_banned(self):
        pass


    def test_create_replies__process__own_audio_clip_is_banned(self):
        pass


    def test_create_replies__process__no_rows(self):

        self.login(self.users[1])

        #proceed

        data = {
            'audio_clip_id': 9999,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        self.assertEqual(request.status_code, 404)


    def test_create_replies__process__only_own_rows_allowed(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[2].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        self.assertEqual(request.status_code, 404)


    def test_create_replies__process__wrong_context_url(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 409)
        self.assertTrue("is_processing" in response_data)
        self.assertTrue("attempts_left" in response_data)

        self.assertTrue(response_data['is_processing'])
        self.assertEqual(
            response_data['attempts_left'],
            settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        )


    def test_create_replies__process__missing_args(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        #proceed

        data = {}

        request = self.client.post(reverse('create_replies_process_api'), data)

        self.assertEqual(request.status_code, 400)


    def test_create_replies__process__faulty_args(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        #proceed

        data = {
            'audio_clip_id': '1a',
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        self.assertEqual(request.status_code, 400)

        data = {
            'audio_clip_id': 'a',
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        self.assertEqual(request.status_code, 400)


    def test_cancel_reply_ok(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())


    def test_cancel_reply_with_missing_args(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_cancel_reply_with_faulty_args(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': 9999,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)


    def test_cancel_reply_but_never_queued_for_it(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)


    def test_cancel_reply_locked_but_not_replying(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertTrue(
            EventReplyQueues.objects.filter(
                locked_for_user=self.users[1],
                event_id=sample_event_0.id
            ).exists()
        )
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())

        self.assertTrue('can_retry' in response_data)
        self.assertFalse(response_data['can_retry'])


    def test_cancel_reply_only_own_rows_allowed(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[2].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[2].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertTrue(EventReplyQueues.objects.filter(locked_for_user=self.users[2], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[2], event_id=sample_event_0.id).exists())


    def test_cancel_reply_but_event_is_banned(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "deleted"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_generic_status_generic_status_name = 'deleted',
            audio_clip_is_banned = True,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())


    def test_cancel_reply_still_processing(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['is_processing'] = True

        cache.set(target_cache_key, target_cache)

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        sample_audio_clip_1.refresh_from_db()

        response_data = get_response_data(request)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 2)
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertEqual(len(target_cache['processings']), 0)


    def test_create_audio_clip_report_ok(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertIsNone(audio_clip_report.last_evaluated)


    def test_create_audio_clip_report_not_ok(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(AudioClipReports.objects.all().count(), 0)


    def test_create_audio_clip_report_missing_args(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        data = {
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 0)


    def test_create_audio_clip_report_faulty_args(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        data = {
            'yolo': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 0)


    def test_create_audio_clip_report_not_found(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': 9999999
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 0)


    def test_create_audio_clip_report_already_reported_before(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            audio_clip_id=sample_audio_clip_0.id,
        )

        time.sleep(2)

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertLess(sample_audio_clip_report_0.last_reported, audio_clip_report.last_reported)


    def test_create_audio_clip_report_already_banned(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_clip_generic_status_generic_status_name = 'deleted',
            audio_clip_is_banned = True,
        )

        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            audio_clip_id=sample_audio_clip_0.id,
            last_evaluated=get_datetime_now(),
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertIsNotNone(audio_clip_report.last_evaluated)


    def test_create_audio_clip_report_self_ok(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[0])

        data = {
            'audio_clip_id': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertIsNone(audio_clip_report.last_evaluated)


    def test_user_block_ok(self):

        self.login(self.users[1])

        data = {
            'username': self.users[0].username,
            'to_block': True
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.all().count(), 1)


    def test_user_block_missing_args(self):

        self.login(self.users[1])

        #start

        data = {
            'username': self.users[0].username,
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.all().count(), 0)

        #start

        data = {
            'to_block': True,
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.all().count(), 0)


    def test_user_block_faulty_args(self):

        self.login(self.users[1])

        #start

        data = {
            'username': self.users[0].username,
            'to_block': '',
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        #200 because bool defaults to False when not passed
        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.all().count(), 0)

        #start

        data = {
            'username': 200,
            'to_block': True,
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        #200 because bool defaults to False when not passed
        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.all().count(), 0)


    def test_user_block__limit_reached(self):

        self.login(self.users[0])

        #fill to limit
        UserBlocks.objects.bulk_create(
            [
                UserBlocks(user=self.users[0], blocked_user=self.users[1]),
                UserBlocks(user=self.users[0], blocked_user=self.users[2]),
            ]
        )

        data = {
            'username': self.users[3].username,
            'to_block': True
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        self.assertEqual(UserBlocks.objects.all().count(), 2)


    def test_user_block__already_blocked(self):

        sample_user_block_0 = UserBlocks.objects.create(
            user_id=self.users[0].id,
            blocked_user_id=self.users[1].id
        )

        self.login(self.users[0])

        data = {
            'username': self.users[1].username,
            'to_block': True
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.all().count(), 1)


    def test_user_block__block_themselves(self):

        self.login(self.users[0])

        data = {
            'username': self.users[0].username,
            'to_block': True
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.all().count(), 0)


    def test_user_block__user_does_not_exist(self):


        self.login(self.users[1])

        data = {
            'username': self.non_existent_username,
            'to_block': True
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.all().count(), 0)


    def test_user_block_unblock_ok(self):

        sample_user_block_0 = UserBlocks.objects.create(
            user_id=self.users[1].id,
            blocked_user_id=self.users[0].id
        )

        self.login(self.users[1])

        data = {
            'username': self.users[0].username,
            'to_block': False
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.all().count(), 0)


    def test_user_block__block_banned_user_ok(self):

        self.login(self.users[0])

        data = {
            'username': self.banned_users[1].username,
            'to_block': True
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.filter(user=self.users[0], blocked_user=self.banned_users[1]).count(), 1)


    def test_user_block__get_has_rows(self):

        self.login(self.users[0])

        UserBlocks.objects.bulk_create([
            UserBlocks(user=self.users[0], blocked_user=self.users[1]),
            UserBlocks(user=self.users[0], blocked_user=self.users[2]),
        ])

        request = self.client.get(reverse('user_blocks_api'))

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(len(response_data['data']), 2)


    def test_user_block__get_no_rows(self):

        self.login(self.users[0])

        request = self.client.get(reverse('user_blocks_api'))

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)
        self.assertEqual(len(response_data['data']), 0)


    def test_user_block__get_has_rows__has_banned_user(self):

        UserBlocks.objects.bulk_create([
            UserBlocks(user=self.users[0], blocked_user=self.users[1]),
            UserBlocks(user=self.users[0], blocked_user=self.banned_users[1]),
        ])

        self.login(self.users[0])

        request = self.client.get(reverse('user_blocks_api'))

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)
        self.assertEqual(len(response_data['data']), 2)


    def test_user_block__get_has_rows__has_only_banned_users(self):

        UserBlocks.objects.bulk_create([
            UserBlocks(user=self.users[0], blocked_user=self.banned_users[1]),
            UserBlocks(user=self.users[0], blocked_user=self.banned_users[2]),
        ])

        self.login(self.users[0])

        request = self.client.get(reverse('user_blocks_api'))

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)
        self.assertEqual(len(response_data['data']), 2)


    def test_user_block__unblock_banned_user(self):

        UserBlocks.objects.bulk_create([
            UserBlocks(user=self.users[0], blocked_user=self.users[1]),
            UserBlocks(user=self.users[0], blocked_user=self.banned_users[1]),
        ])

        self.login(self.users[0])

        data = {
            'username': self.banned_users[1].username,
            'to_block': False
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.all().count(), 1)


    def test_audio_clip_like_dislike_missing_args(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        #bool defaults to False by serializer
        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        data = {
            'is_liked': True,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_audio_clip_like_dislike_faulty_args(self):


        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        #0 and 1 are considered as valid bool by DRF serializer
        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': 1,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': 2,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        data = {
            'audio_clip_id': 999,
            'is_liked': True,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_create_and_delete_audio_clip_like(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 1)
        self.assertEqual(sample_audio_clip_0.like_ratio, 1)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertTrue(audio_clip_like_dislike.is_liked)

        #undo

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': json.dumps(None)
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)


    def test_create_and_delete_audio_clip_dislike(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': False
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 1)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertFalse(audio_clip_like_dislike.is_liked)

        #undo

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': json.dumps(None)
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)


    def test_random_audio_clip_like_dislike_chaining(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #start

        self.login(self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 1)
        self.assertEqual(sample_audio_clip_0.like_ratio, 1)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertTrue(audio_clip_like_dislike.is_liked)

        #switch

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': False
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 1)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertFalse(audio_clip_like_dislike.is_liked)

        #switch again

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 1)
        self.assertEqual(sample_audio_clip_0.like_ratio, 1)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertTrue(audio_clip_like_dislike.is_liked)

        #random resiliency test
        #reset to None

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': json.dumps(None)
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        self.assertEqual(sample_audio_clip_0.like_count, 0)
        self.assertEqual(sample_audio_clip_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)

        #like

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_0.like_count, 1)
        self.assertEqual(sample_audio_clip_0.like_ratio, 1)
        self.assertEqual(sample_audio_clip_0.dislike_count, 0)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertTrue(audio_clip_like_dislike.is_liked)


    def test_random_audio_clip_like_dislike_chaining_multiple_users(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        def do_request(target_user, is_liked:bool|None):

            self.login(target_user)

            data = {
                'audio_clip_id': sample_audio_clip_0.id,
                'is_liked': json.dumps(is_liked)
            }

            request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

            self.assertEqual(request.status_code, 200)

        #we randomise between True/False/None, among users
        #we then track it and see if db accurately reflects it

        possible_is_liked_values = [True, False, None]

        users_latest_is_liked = {}

        for user in self.users:

            users_latest_is_liked.update({
                user.id: None
            })

        #start

        for test_loop in range(0, 10):

            #randomise is_liked and make request for every user

            for user in self.users:

                is_liked = possible_is_liked_values[random.randint(0, 2)]

                do_request(user, is_liked)

                users_latest_is_liked.update({
                    user.id: is_liked
                })

        #check

        sample_audio_clip_0.refresh_from_db()

        audio_clip_likes_dislikes = AudioClipLikesDislikes.objects.all()

        is_liked_total_count = {
            'true': 0,
            'false': 0,
        }

        for row in audio_clip_likes_dislikes:

            if row.is_liked is True:
                is_liked_total_count['true'] += 1
            elif row.is_liked is False:
                is_liked_total_count['false'] += 1

            if row.is_liked != users_latest_is_liked[row.user_id]:

                raise AssertionError('is_liked did not match.')

        self.assertEqual(sample_audio_clip_0.like_count, is_liked_total_count['true'])
        self.assertEqual(sample_audio_clip_0.dislike_count, is_liked_total_count['false'])


    def test_list_audio_clip_processing__ok(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        request = self.client.get(
            reverse(
                'list_audio_clip_processings_api',
            )
        )

        response_data = get_response_data(request)
        self.assertEqual(len(response_data['data']['processings']), 1)
        self.assertEqual(
            response_data['data']['processings'][str(sample_audio_clip_0.id)]['attempts_left'],
            settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        )
        self.assertEqual(response_data['data']['processings'][str(sample_audio_clip_0.id)]['is_processing'], True)


    def test_list_audio_clip_processing__only_own_rows_allowed(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        request = self.client.get(
            reverse(
                'list_audio_clip_processings_api',
            )
        )

        response_data = get_response_data(request)
        self.assertEqual(len(response_data['data']['processings']), 0)


    def test_list_audio_clip_processing__not_processing(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_main_object()

        cache.set(target_cache_key, target_cache)

        request = self.client.get(
            reverse(
                'list_audio_clip_processings_api',
            )
        )

        response_data = get_response_data(request)
        self.assertEqual(len(response_data['data']['processings']), 0)


    def test_list_audio_clip_processing__no_rows(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )

        request = self.client.get(
            reverse(
                'list_audio_clip_processings_api',
            )
        )

        #expect default cache to be auto-created

        response_data = get_response_data(request)
        self.assertEqual(len(response_data['data']['processings']), 0)


    def test_check_audio_clip_processing__still_processing(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['is_processing'] = True

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.get(
            reverse(
                'check_audio_clip_processings_api',
                kwargs=data
            )
        )

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 409)
        self.assertTrue('is_processing' in response_data)
        self.assertTrue('attempts_left' in response_data)

        self.assertTrue(response_data['is_processing'])
        self.assertEqual(
            response_data['attempts_left'],
            settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        )


    def test_check_audio_clip_processing__failed_can_reattempt(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['is_processing'] = False

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.get(
            reverse(
                'check_audio_clip_processings_api',
                kwargs=data
            )
        )
        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 200)
        self.assertTrue('is_processing' in response_data)
        self.assertTrue('attempts_left' in response_data)

        self.assertFalse(response_data['is_processing'])
        self.assertEqual(
            response_data['attempts_left'],
            settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        )


    def test_check_audio_clip_processing__failed_cannot_reattempt(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='deleted',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing_max_attempts_reached',
        )

        #no cache

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.get(
            reverse(
                'check_audio_clip_processings_api',
                kwargs=data
            )
        )
        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 404)
        print(response_data)


    def test_check_audio_clip_processing__already_processed(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #no cache

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.get(
            reverse(
                'check_audio_clip_processings_api',
                kwargs=data
            )
        )
        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 200)
        self.assertTrue('is_processed' in response_data)


    def test_check_audio_clip_processing__only_own_rows_allowed(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['is_processing'] = True

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.get(
            reverse(
                'check_audio_clip_processings_api',
                kwargs=data
            )
        )
        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 404)


    def test_check_audio_clip_processing__no_row(self):

        self.login(self.users[0])

        #proceed

        data = {
            'audio_clip_id': 99999999,
        }

        request = self.client.get(
            reverse(
                'check_audio_clip_processings_api',
                kwargs=data
            )
        )
        self.assertEqual(request.status_code, 404)


    def test_check_audio_clip_processing__faulty_args(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_1 = EventsFactory(
            event_created_by=self.users[1],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        #no cache

        #proceed

        #not own audio clip
        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.get(
            reverse(
                'check_audio_clip_processings_api',
                kwargs=data
            )
        )
        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 404)


    def test_originator__delete_audio_clip_processing__ok(self):

        self.login(self.users[0])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['is_processing'] = True

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('delete_audio_clip_processings_api'), data)

        self.assertTrue(request.status_code, 200)
        self.assertFalse(Events.objects.filter(pk=sample_event_0.id).exists())
        self.assertFalse(AudioClips.objects.filter(pk=sample_audio_clip_0.id).exists())

        target_cache = cache.get(target_cache_key)

        self.assertIsNone(target_cache['processings'].get(str(sample_audio_clip_0.id), None))


    def test_originator__delete_audio_clip_processing__only_own_rows_allowed(self):

        self.login(self.users[1])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['is_processing'] = True

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('delete_audio_clip_processings_api'), data)

        self.assertTrue(request.status_code, 404)
        self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
        self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_0.id).exists())

        target_cache = cache.get(target_cache_key)

        self.assertIsNotNone(target_cache['processings'].get(str(sample_audio_clip_0.id), None))


    def test_originator__delete_audio_clip_processing__not_processing(self):

        self.login(self.users[0])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'deleted',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_main_object()

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('delete_audio_clip_processings_api'), data)

        self.assertTrue(request.status_code, 200)
        self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
        self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_0.id).exists())

        target_cache = cache.get(target_cache_key)

        self.assertIsNone(target_cache['processings'].get(str(sample_audio_clip_0.id), None))


    def test_originator__delete_audio_clip_processing__no_rows(self):

        self.login(self.users[0])

        #prepare data

        #proceed

        data = {
            'audio_clip_id': 9999999999,
        }

        request = self.client.post(reverse('delete_audio_clip_processings_api'), data)

        self.assertTrue(request.status_code, 404)


    def test_responder__delete_audio_clip_processing__ok(self):

        self.login(self.users[1])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['is_processing'] = True

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('delete_audio_clip_processings_api'), data)

        self.assertTrue(request.status_code, 200)
        self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
        self.assertFalse(AudioClips.objects.filter(pk=sample_audio_clip_1.id).exists())
        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())

        target_cache = cache.get(target_cache_key)

        self.assertIsNone(target_cache['processings'].get(str(sample_audio_clip_1.id), None))


    def test_responder__delete_audio_clip_processing__only_own_rows_allowed(self):


        self.login(self.users[2])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
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

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['is_processing'] = True

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('delete_audio_clip_processings_api'), data)

        self.assertTrue(request.status_code, 404)
        self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
        self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_1.id).exists())
        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())

        target_cache = cache.get(target_cache_key)

        self.assertIsNotNone(target_cache['processings'].get(str(sample_audio_clip_1.id), None))


    def test_responder__delete_audio_clip_processing__not_processing(self):

        self.login(self.users[1])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'completed',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_main_object()

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('delete_audio_clip_processings_api'), data)

        self.assertTrue(request.status_code, 404)
        self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
        self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_1.id).exists())
        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())

        target_cache = cache.get(target_cache_key)

        self.assertIsNone(target_cache['processings'].get(str(sample_audio_clip_0.id), None))


    def test_responder__delete_audio_clip_processing__no_rows(self):

        self.login(self.users[1])

        #prepare data

        #proceed

        data = {
            'audio_clip_id': 9999999999,
        }

        request = self.client.post(reverse('delete_audio_clip_processings_api'), data)

        self.assertTrue(request.status_code, 404)


    def test_user_following__follow_user_ok(self):

        self.login(self.users[0])

        data = {
            'username': self.users[1].username,
            'to_follow': True
        }

        request = self.client.post(reverse('user_follows_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.all().count(), 1)


    def test_user_following__already_following(self):

        UserFollows.objects.create(user=self.users[0], followed_user=self.users[1])

        self.login(self.users[0])

        data = {
            'username': self.users[1].username,
            'to_follow': True
        }

        request = self.client.post(reverse('user_follows_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.all().count(), 1)


    def test_user_following__limit_reached(self):

        UserFollows.objects.bulk_create(
            [
                UserFollows(user=self.users[0], followed_user=self.users[1]),
                UserFollows(user=self.users[0], followed_user=self.users[2]),
            ]
        )

        self.login(self.users[0])

        data = {
            'username': self.users[3].username,
            'to_follow': True
        }

        request = self.client.post(reverse('user_follows_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.all().count(), 2)


    def test_user_following__follow_themselves(self):

        self.login(self.users[0])

        data = {
            'username': self.users[0].username,
            'to_follow': True
        }

        request = self.client.post(reverse('user_follows_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.all().count(), 0)


    def test_user_following__user_does_not_exist(self):

        self.login(self.users[0])

        data = {
            'username': self.non_existent_username,
            'to_follow': True
        }

        request = self.client.post(reverse('user_follows_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.all().count(), 0)


    def test_user_following__follow_user_missing_args(self):

        self.login(self.users[0])

        data = {
            'to_follow': True
        }

        request = self.client.post(reverse('user_follows_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.all().count(), 0)

        #again

        data = {
            'username': self.users[1].username,
        }

        request = self.client.post(reverse('user_follows_api'), data)

        #check

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.all().count(), 0)


    def test_user_following__follow_user_faulty_args(self):

        self.login(self.users[0])

        data = {
            'username': 200,
            'to_follow': True
        }

        request = self.client.post(reverse('user_follows_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.all().count(), 0)

        #again

        data = {
            'username': self.users[1].username,
            'to_follow': 200,
        }

        request = self.client.post(reverse('user_follows_api'), data)

        #check

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.all().count(), 0)


    def test_user_following__get_no_rows(self):

        self.login(self.users[0])

        request = self.client.get(reverse('user_follows_api'))

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(response_data['data'], [])


    def test_user_following__get_has_rows(self):

        UserFollows.objects.bulk_create(
            [
                UserFollows(user=self.users[0], followed_user=self.users[1]),
                UserFollows(user=self.users[0], followed_user=self.users[2]),
            ]
        )

        self.login(self.users[0])

        request = self.client.get(reverse('user_follows_api'))

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(len(response_data['data']), 2)

        #ensure no id leaked
        self.assertFalse('user_id' in response_data['data'][0])
        self.assertFalse('followed_user_id' in response_data['data'][0])


    def test_user_following__follow_user_is_banned(self):

        self.login(self.users[0])

        data = {
            'username': self.banned_users[1].username,
            'to_follow': True
        }

        request = self.client.post(reverse('user_follows_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.all().count(), 1)


    def test_user_following__get_has_rows__has_banned_user(self):

        UserFollows.objects.bulk_create(
            [
                UserFollows(user=self.users[0], followed_user=self.users[1]),
                UserFollows(user=self.users[0], followed_user=self.banned_users[1]),
            ]
        )

        self.login(self.users[0])

        request = self.client.get(reverse('user_follows_api'))

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(len(response_data['data']), 2)


    def test_user_following__get_has_rows__all_banned_users(self):

        UserFollows.objects.bulk_create(
            [
                UserFollows(user=self.users[0], followed_user=self.banned_users[1]),
                UserFollows(user=self.users[0], followed_user=self.banned_users[2]),
            ]
        )

        self.login(self.users[0])

        request = self.client.get(reverse('user_follows_api'))

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(len(response_data['data']), 2)


    def test_user_following__unfollow(self):

        UserFollows.objects.bulk_create(
            [
                UserFollows(user=self.users[0], followed_user=self.users[1]),
                UserFollows(user=self.users[0], followed_user=self.users[2]),
            ]
        )

        self.login(self.users[0])

        data = {
            'username': self.users[2].username,
            'to_follow': False
        }

        request = self.client.post(reverse('user_follows_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.filter(followed_user=self.users[2]).count(), 0)
        self.assertEqual(UserFollows.objects.all().count(), 1)


    def test_user_following__unfollow_banned_user(self):

        UserFollows.objects.bulk_create(
            [
                UserFollows(user=self.users[0], followed_user=self.users[1]),
                UserFollows(user=self.users[0], followed_user=self.banned_users[2]),
            ]
        )

        self.login(self.users[0])

        data = {
            'username': self.banned_users[2].username,
            'to_follow': False
        }

        request = self.client.post(reverse('user_follows_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.filter(followed_user=self.banned_users[2]).count(), 0)
        self.assertEqual(UserFollows.objects.all().count(), 1)



#these involve AWS in one way or another
@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    DEBUG=True,
    CELERY_TASK_ALWAYS_EAGER=True,
)
class Core_NormaliseAudioClips_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

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
            'voicewake/tests/file_samples/txt_as_fake_webm.webm'
        )

        #files
        with open(cls.shorter_audio_file_full_path, 'rb') as file_stream:
            cls.shorter_audio_file = SimpleUploadedFile('sample_audio_file.webm', file_stream.read(), 'audio/webm')

        #objects in s3 should exist before starting tests

        #unprocessed/processed object keys
        cls.unprocessed_object_key = 'test/test0.webm'
        cls.processed_object_key = 'test/test0.mp3'

        #ensure test files exist in s3 before we run tests
        cls._prepare_s3_unprocessed_audio_file(
            unprocessed_object_key=cls.unprocessed_object_key,
            file_extension='webm',
            local_file_path=cls.shorter_audio_file_full_path
        )

        #ensure faulty file exists
        cls.faulty_audio_file_unprocessed_object_key = 'test/test1.webm'
        cls.faulty_audio_file_processed_object_key = 'test/test1.mp3'

        cls._prepare_s3_unprocessed_audio_file(
            unprocessed_object_key=cls.faulty_audio_file_unprocessed_object_key,
            file_extension='webm',
            local_file_path=cls.faulty_audio_file_full_path
        )


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


    def create_event_reply_queue(self, event_id:int, locked_for_user_id:int, is_replying:bool, when_locked:datetime):

        return EventReplyQueues.objects.create(
            event_id=event_id,
            locked_for_user_id=locked_for_user_id,
            is_replying=is_replying,
            when_locked=when_locked
        )


    def create_user_event(self, user_id:int, event_id:int, when_excluded_for_reply:datetime):

        return UserEvents.objects.create(
            user_id=user_id,
            event_id=event_id,
            when_excluded_for_reply=when_excluded_for_reply
        )


    @staticmethod
    def _prepare_s3_unprocessed_audio_file(
        unprocessed_object_key:str,
        file_extension:str,
        local_file_path:str,
        force_upload:bool=False,
    ):

        s3_wrapper_class = S3PostWrapper(
            is_ec2=False,
            allowed_unprocessed_file_extensions=settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=int(os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B']),
            url_expiry_s=int(os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S']),
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        if force_upload is False:

            object_exists = s3_wrapper_class.check_object_exists(key=unprocessed_object_key)

            if object_exists is True:

                print(unprocessed_object_key + ' exists. Continuing...')
                return

        #upload

        upload_info = s3_wrapper_class.generate_unprocessed_presigned_post_url(
            key=unprocessed_object_key,
            file_extension=file_extension,
        )

        S3PostWrapper.s3_post_upload(
            url=upload_info['url'],
            fields=upload_info['fields'],
            local_file_path=local_file_path,
        )


    def test_lambda_normalise_audio_clips_ok(self):

        #swap the unprocessed test file in s3 here
        # self._prepare_s3_unprocessed_audio_file(
        #     unprocessed_object_key=self.unprocessed_object_key,
        #     file_extension='webm',
        #     local_file_path=self.shorter_audio_file_full_path,
        #     force_upload=True
        # )

        lambda_wrapper = AWSLambdaWrapper(
            is_ec2=False,
            timeout_s=int(os.environ['AWS_LAMBDA_NORMALISE_TIMEOUT_S']),
            region_name=os.environ['AWS_LAMBDA_REGION_NAME'],
            aws_access_key_id=os.environ['AWS_LAMBDA_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_LAMBDA_SECRET_ACCESS_KEY'],
        )

        lambda_response_data = lambda_wrapper.invoke_normalise_audio_clips_lambda(
            s3_region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_object_key=self.unprocessed_object_key,
            processed_object_key=self.processed_object_key,
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            processed_bucket_name=os.environ['AWS_S3_MEDIA_BUCKET_NAME'],
        )

        print(lambda_response_data)

        #optimisation notes
            #normalisation is the only truly expensive step
                #e.g.:
                    #sample A (10s, 168kb, 128mb memory)
                        # {
                        #     'retrieve_unprocessed_audio_file': 0.561773,
                        #     'prepare_info_before_normalise': 0.060362,
                        #     'normalise_and_overwrite_audio_file': 9.418502,
                        #     'get_duration_after_normalise': 0.078297,
                        #     'get_peaks_by_buckets': 0.541153,
                        #     'store_processed_audio_file': 0.619966
                        # }
                        #cold start test case duration: 27s
                        #warm start test case duration: 16s
                    #sample B (120s, 1.85mb, 512mb memory)
                        # {
                        #     'retrieve_unprocessed_audio_file': 0.254644,
                        #     'prepare_info_before_normalise': 0.54729,
                        #     'normalise_and_overwrite_audio_file': 25.239503,
                        #     'get_duration_after_normalise': 0.024484,
                        #     'get_peaks_by_buckets': 1.093865,
                        #     'store_processed_audio_file': 0.265412
                        # }
                        #cold start test case duration: 35s
                        #warm start test case duration: 32s
            #memory results for processing 10s and maximum 120s:
                #tested with 3 tries
                    #on memory change, first try is always slower, and 2nd and 3rd are almost the same
                #128mb
                    #168kb: 9s normalise, cold 27s, warm 16s
                    #1.85mb: >60s, timed out
                #512mb
                    #168kb: 2.5s normalise, cold 11s, warm 8s
                    #1.85mb: 25s normalise, cold 35s, warm 32s
                #1024mb
                    #168kb: 1.4s normalise, cold 8s, warm 6s
                    #1.85mb: 12s normalise, cold 20s, warm 18s
                #1536mb
                    #168kb: 0.9s normalise, cold 7s, warm 6s
                    #1.85mb: 8s normalise, cold 15s, warm 13s
                #conclusion
                    #not urgent
                    #1536mb memory at 3*512mb took 8s instead of 6s to normalise
                    #1024mb is the winner


    def test_create_events__process__ok(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
            audio_clip_audio_file=self.unprocessed_object_key,
        )

        #let fresh cache be auto-created when it doesn't exist, and use it

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)
        request_data = get_response_data(request)

        self.assertEqual(request.status_code, 200)

        sample_audio_clip_0.refresh_from_db()

        self.assertEqual(
            sample_audio_clip_0.generic_status.generic_status_name,
            'ok'
        )
        self.assertEqual(
            sample_audio_clip_0.audio_file,
            self.processed_object_key
        )

        #don't evaluate actual value, as it is always -1 in test, but has late -1 in prod due to the nature of task queue
        self.assertTrue('attempts_left' in request_data)


    def test_create_events__process__reattempt_ok(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
            audio_clip_audio_file=self.unprocessed_object_key,
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

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 2
        target_cache['processings'][str(sample_audio_clip_0.id)]['is_processing'] = False

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        self.assertEqual(request.status_code, 200)

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertEqual(len(target_cache['processings']), 0)


    def test_create_events__process__last_reattempt_failed(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
            audio_clip_audio_file=self.faulty_audio_file_unprocessed_object_key,
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

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['is_processing'] = False

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()

        self.assertEqual(request.status_code, 200)
        self.assertEqual(
            sample_event_0.generic_status.generic_status_name,
            'deleted'
        )
        self.assertEqual(
            sample_audio_clip_0.generic_status.generic_status_name,
            'processing_max_attempts_reached'
        )

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertEqual(len(target_cache['processings']), 0)


    def test_create_replies__process__ok(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=self.users[1].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
            audio_clip_audio_file=self.unprocessed_object_key,
        )

        #let fresh cache be auto-created when it doesn't exist, and use it

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)
        request_data = get_response_data(request)

        self.assertEqual(request.status_code, 200)

        sample_audio_clip_1.refresh_from_db()

        self.assertEqual(
            sample_audio_clip_1.generic_status.generic_status_name,
            'ok'
        )
        self.assertEqual(
            sample_audio_clip_1.audio_file,
            self.processed_object_key
        )
        self.assertFalse(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )

        #don't evaluate actual value, as it is always -1 in test, but has late -1 in prod due to the nature of task queue
        self.assertTrue('attempts_left' in request_data)


    def test_create_replies__process__reattempt_ok(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
            audio_clip_audio_file=self.unprocessed_object_key,
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

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        self.assertEqual(request.status_code, 200)
        self.assertFalse(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertEqual(len(target_cache['processings']), 0)


    def test_create_replies__process__last_reattempt_failed(self):

        self.login(self.users[1])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
            audio_clip_audio_file=self.faulty_audio_file_unprocessed_object_key,
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

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] = 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['is_processing'] = False

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        sample_event_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()

        self.assertEqual(request.status_code, 200)
        self.assertEqual(
            sample_event_0.generic_status.generic_status_name,
            'incomplete'
        )
        self.assertEqual(
            sample_audio_clip_1.generic_status.generic_status_name,
            'processing_max_attempts_reached'
        )
        self.assertFalse(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertEqual(len(target_cache['processings']), 0)


























































