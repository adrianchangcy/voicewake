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



#tests always auto-override DEBUG to False
#manually specify it as True via @override_settings as needed



def ensure_otp_is_always_wrong(otp):

    if int(otp[0]) == 0:
        otp = '1' + otp[1:]
    else:
        otp = str(int(otp[0]) - 1) + otp[1:]

    return otp



@override_settings(
    
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
            s3_audio_file_max_size_b=settings.AWS_S3_AUDIO_FILE_MAX_SIZE_B,
            url_expiry_s=settings.AWS_S3_UPLOAD_URL_EXPIRY_S,
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
            s3_audio_file_max_size_b=settings.AWS_S3_AUDIO_FILE_MAX_SIZE_B,
            url_expiry_s=settings.AWS_S3_UPLOAD_URL_EXPIRY_S,
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
            s3_audio_file_max_size_b=settings.AWS_S3_AUDIO_FILE_MAX_SIZE_B,
            url_expiry_s=settings.AWS_S3_UPLOAD_URL_EXPIRY_S,
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
            s3_audio_file_max_size_b=settings.AWS_S3_AUDIO_FILE_MAX_SIZE_B,
            url_expiry_s=settings.AWS_S3_UPLOAD_URL_EXPIRY_S,
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
            s3_audio_file_max_size_b=settings.AWS_S3_AUDIO_FILE_MAX_SIZE_B,
            url_expiry_s=settings.AWS_S3_UPLOAD_URL_EXPIRY_S,
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
            timeout_s=settings.AWS_LAMBDA_NORMALISE_TIMEOUT_S,
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


    def test_sign_up_ok(self, another_email=''):

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

        #check

        self.assertFalse(user_instance.is_active)

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

        user_instance.refresh_from_db()

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

        self.test_sign_up_ok()

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

        target_user = get_user_model().objects.get(
            email_lowercase=self.email.lower()
        )

        #user should be created with only email
        self.assertFalse(target_user.is_active)

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


    def test_log_in_ok(self):

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

        #check

        self.assertTrue(user_instance.is_active)

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

        user_instance.refresh_from_db()

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

        self.test_log_in_ok()

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

        self.test_log_in_ok()

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

        self.test_log_in_ok()

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

        self.test_sign_up_ok(another_email)

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

        # audio_clip_audio_file='audio-clips/year_2023/month_7/day_21/user_id_1/e_13.webm'

        handle_audio_file_class = AWSLambdaNormaliseAudioClips(
            is_lambda=False,
            s3_region_name=os.environ['AWS_S3_REGION_NAME'],
            s3_aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            s3_aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
            processed_file_extension=settings.AUDIO_CLIP_PROCESSED_FILE_EXTENSION,
            use_timer=True,
        )

        print(handle_audio_file_class.main())



#should use FactoryBoy to prevent future changes from requiring every individual test case to be edited
#see if we can make reverse() use NGINX base url
@override_settings(
    MEDIA_ROOT=os.path.join(settings.BASE_DIR, 'voicewake/tests'),
    CELERY_TASK_ALWAYS_EAGER=True,
    USER_BLOCKS_LIMIT=2,
    USER_FOLLOWS_LIMIT=2,
)
class Core_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

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


    def get_audio_file(self):

        #need this to auto-reset via seek(0)
        self.audio_file.seek(0)
        return self.audio_file


    def get_bad_file(self):

        #need this to auto-reset via seek(0)
        self.bad_file.seek(0)
        return self.bad_file


    def create_user(self):

        random_string = get_random_string(10)

        current_user = get_user_model().objects.create_user(
            username='useR'+random_string,
            email='user'+random_string+'@gmail.com',
        )

        current_user = get_user_model().objects.get(username_lowercase="user"+random_string)

        current_user.is_active = True
        current_user.save()

        return current_user


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


    def test_create_events__upload__ok(self):

        self.login(self.users[0])

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        print_with_function_name(request.content)
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

        event = Events.objects.get(pk=response_data['event_id'])
        self.assertEqual(event.generic_status.generic_status_name, 'processing')
        self.assertEqual(event.created_by_id, self.users[0].id)
        self.assertEqual(event.event_name, data['event_name'])

        audio_clip = AudioClips.objects.get(pk=response_data['audio_clip_id'])
        self.assertEqual(audio_clip.generic_status.generic_status_name, 'processing_pending')
        self.assertEqual(audio_clip.user_id, self.users[0].id)
        self.assertEqual(audio_clip.audio_clip_tone_id, data['audio_clip_tone_id'])
        self.assertEqual(audio_clip.event.id, event.id)
        self.assertGreater(len(audio_clip.audio_file), 0)
        self.assertEqual(audio_clip.audio_duration_s, 0)
        self.assertEqual(len(audio_clip.audio_volume_peaks), 0)

        self.assertTrue(AudioClipMetrics.objects.filter(audio_clip_id=audio_clip.id).exists())

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

            self.assertEqual(audio_clip.generic_status.generic_status_name, 'processing_pending')
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
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print_with_function_name(request.content)
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
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_PROCESSED_FILE_EXTENSION,
            audio_clip_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 404)


    def test_create_events__regenerate_upload_url__own_audio_clip_is_deleted(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #delete, should fail

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 400)

        #proceed

        self.login(self.users[0])

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('key' in json.loads(response_data['upload_fields']))
        self.assertFalse('event_id' in response_data)
        self.assertFalse('audio_clip_id' in response_data)


    def test_create_events__regenerate_upload_url__own_audio_clip_is_banned(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #ban, should fail

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        self.assertEqual(request.status_code, 400)

        #proceed

        self.login(self.users[0])

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('key' in json.loads(response_data['upload_fields']))
        self.assertFalse('event_id' in response_data)
        self.assertFalse('audio_clip_id' in response_data)


    def test_create_events__regenerate_upload_url__missing_args(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #proceed

        data = {}

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 400)


    def test_create_events__regenerate_upload_url__faulty_args(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_PROCESSED_FILE_EXTENSION,
            audio_clip_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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


    def test_create_events__process__processing(self):

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_event_0,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        response_data = get_response_data(request)

        print(request.content)
        self.assertEqual(request.status_code, 409)
        self.assertEqual(response_data['status'], 'processing')


    def test_create_events__process__processing__overdue(self):

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        sample_audio_clip_0.when_created = get_datetime_now() - timedelta(seconds=settings.AUDIO_CLIP_UNPROCESSED_EXPIRY_S + 2)
        sample_audio_clip_0.save()

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_event_0,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        response_data = get_response_data(request)

        print(request.content)
        self.assertEqual(request.status_code, 409)
        self.assertEqual(response_data['status'], 'processing')


    def test_create_events__process__overdue(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing_failed',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        sample_audio_clip_0.when_created = get_datetime_now() - timedelta(seconds=settings.AUDIO_CLIP_UNPROCESSED_EXPIRY_S + 2)
        sample_audio_clip_0.save()

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_event_0,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        response_data = get_response_data(request)

        print(request.content)
        self.assertEqual(request.status_code, 404)


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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 404)


    def test_create_event__process__processing__attempt_deletion(self):

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_0.event,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #delete, should fail

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 400)

        #processing should still be allowed

        self.login(self.users[0])

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        response_data = get_response_data(request)
        print(request.content)

        self.assertEqual(request.status_code, 409)
        self.assertTrue("attempts_left" in response_data)
        self.assertEqual(response_data['status'], 'processing')
        self.assertEqual(
            response_data['attempts_left'],
            settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        )


    def test_create_event__process__processing__attempt_ban(self):

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_0.event,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #ban, should fail

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            },
        )

        self.assertEqual(request.status_code, 400)

        #processing should still be allowed

        self.login(self.users[0])

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 409)
        self.assertTrue("attempts_left" in response_data)
        self.assertEqual(response_data['status'], 'processing')
        self.assertEqual(
            response_data['attempts_left'],
            settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        )


    def test_create_event__process__processing_failed__attempt_deletion(self):

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'processing',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing_failed',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_0.event,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #delete, should fail

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 400)

        #no change

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        target_cache = cache.get(target_cache_key, None)

        sample_event_0.generic_status.generic_status_name = 'processing'
        sample_audio_clip_0.generic_status.geneic_status_name = 'processing_failed'
        self.assertIsNotNone(CreateAudioClips.get_processing_object_from_processing_cache(target_cache, sample_audio_clip_0.id))


    def test_create_event__process__processing_failed__attempt_ban(self):

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing_failed',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_0.event,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #ban, should fail

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            },
        )

        self.assertEqual(request.status_code, 400)

        #no change

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        self.users[0].refresh_from_db()
        target_cache = cache.get(target_cache_key, None)

        sample_event_0.generic_status.generic_status_name = 'processing'
        sample_audio_clip_0.generic_status.geneic_status_name = 'processing_failed'
        self.assertIsNotNone(CreateAudioClips.get_processing_object_from_processing_cache(target_cache, sample_audio_clip_0.id))
        self.assertFalse(self.users[0].is_banned)


    def test_create_events__process__missing_args(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_PROCESSED_FILE_EXTENSION,
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_audio_file='yolofolder/yolofile.' + settings.AUDIO_CLIP_PROCESSED_FILE_EXTENSION,
            audio_clip_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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


    def test_get_event_incomplete__ok(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertTrue('event' in response_data[0])
        self.assertTrue('originator' in response_data[0])
        self.assertTrue('responder' in response_data[0])
        self.assertFalse('event_reply_queue' in response_data[0])

        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)


    def test_get_event__incomplete__has_event_reply_queue__same_request_user__not_replying(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertTrue('event_reply_queue' in response_data[0])
        self.assertFalse(response_data[0]['event_reply_queue']['is_replying'])


    def test_get_event__incomplete__has_event_reply_queue__same_request_user__is_replying(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertTrue('event_reply_queue' in response_data[0])
        self.assertTrue(response_data[0]['event_reply_queue']['is_replying'])


    def test_get_event__incomplete__has_event_reply_queue__different_request_user__not_replying(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertFalse('event_reply_queue' in response_data[0])


    def test_get_event__incomplete__has_event_reply_queue__different_request_user__is_replying(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertFalse('event_reply_queue' in response_data[0])


    def test_get_event__incomplete__has_event_reply_queue__not_replying__only_responder_can_get_queue(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )
        sample_event_reply_queue_1 = self.create_event_reply_queue(
            event_id=sample_event_1.id,
            locked_for_user_id=self.users[3].id,
            is_replying=False,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )
        sample_user_event_1 = self.create_user_event(
            self.users[3].id,
            sample_event_1.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #get as anonymous user

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertFalse('event_reply_queue' in response_data[0])

        #get as originator

        self.login(self.users[0])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertFalse('event_reply_queue' in response_data[0])

        #get as any random irrelevant user

        self.login(self.users[2])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertFalse('event_reply_queue' in response_data[0])

        #get as different responder

        self.login(self.users[3])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertFalse('event_reply_queue' in response_data[0])

        #get as correct responder

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertTrue('event_reply_queue' in response_data[0])


    def test_get_event__incomplete__has_event_reply_queue__is_replying__only_responder_can_get_queue(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )
        sample_event_reply_queue_1 = self.create_event_reply_queue(
            event_id=sample_event_1.id,
            locked_for_user_id=self.users[3].id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )
        sample_user_event_1 = self.create_user_event(
            self.users[3].id,
            sample_event_1.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        #get as anonymous user

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertFalse('event_reply_queue' in response_data[0])

        #get as originator

        self.login(self.users[0])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertFalse('event_reply_queue' in response_data[0])

        #get as any random irrelevant user

        self.login(self.users[2])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertFalse('event_reply_queue' in response_data[0])

        #get as different responder

        self.login(self.users[3])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertFalse('event_reply_queue' in response_data[0])

        #get as correct responder

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.get(
            reverse(
                'get_events_api',
                kwargs=data
            )
        )

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 0)
        self.assertTrue('event_reply_queue' in response_data[0])


    def test_get_event__incomplete__no_audio_clips(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
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
        print_with_function_name(request.content)

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 0)


    def test_get_event__completed__ok(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="completed",
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
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertTrue('event' in response_data[0])
        self.assertTrue('originator' in response_data[0])
        self.assertTrue('responder' in response_data[0])
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 1)
        self.assertEqual(response_data[0]['responder'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['responder'][0]['user']['username'], sample_audio_clip_1.user.username)
        self.assertEqual(response_data[0]['responder'][0]['generic_status']['generic_status_name'], sample_audio_clip_1.generic_status.generic_status_name)
        self.assertFalse('event_reply_queue' in response_data[0])


    def test_get_event__completed__deleted_same_responders(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="completed",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_generic_status_generic_status_name='deleted',
            audio_clip_is_banned=False,
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_generic_status_generic_status_name='deleted',
            audio_clip_is_banned=True,
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_3 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )
        sample_audio_clip_metric_2 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_2,
        )
        sample_audio_clip_metric_3 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_3,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertTrue('event' in response_data[0])
        self.assertTrue('originator' in response_data[0])
        self.assertTrue('responder' in response_data[0])
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 1)
        self.assertEqual(response_data[0]['responder'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['responder'][0]['user']['username'], sample_audio_clip_3.user.username)
        self.assertEqual(response_data[0]['responder'][0]['generic_status']['generic_status_name'], sample_audio_clip_3.generic_status.generic_status_name)
        self.assertFalse('event_reply_queue' in response_data[0])


    def test_get_event__completed__deleted_different_responders(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="completed",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_generic_status_generic_status_name='deleted',
            audio_clip_is_banned=False,
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_generic_status_generic_status_name='deleted',
            audio_clip_is_banned=True,
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_3 = AudioClipsFactory(
            audio_clip_user=self.users[3],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )
        sample_audio_clip_metric_2 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_2,
        )
        sample_audio_clip_metric_3 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_3,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 1)
        self.assertTrue('event' in response_data[0])
        self.assertTrue('originator' in response_data[0])
        self.assertTrue('responder' in response_data[0])
        self.assertEqual(response_data[0]['event']['id'], sample_event_0.id)
        self.assertEqual(len(response_data[0]['originator']), 1)
        self.assertEqual(response_data[0]['originator'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['originator'][0]['user']['username'], sample_audio_clip_0.user.username)
        self.assertEqual(response_data[0]['originator'][0]['generic_status']['generic_status_name'], sample_audio_clip_0.generic_status.generic_status_name)
        self.assertEqual(len(response_data[0]['responder']), 1)
        self.assertEqual(response_data[0]['responder'][0]['event_id'], sample_event_0.id)
        self.assertEqual(response_data[0]['responder'][0]['user']['username'], sample_audio_clip_3.user.username)
        self.assertEqual(response_data[0]['responder'][0]['generic_status']['generic_status_name'], sample_audio_clip_3.generic_status.generic_status_name)
        self.assertFalse('event_reply_queue' in response_data[0])


    def test_get_event__completed__no_audio_clips(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="completed",
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
        print_with_function_name(request.content)

        response_data = get_response_data(request)['data']

        self.assertEqual(len(response_data), 0)


    def test_list_event_reply_choices_daily_limit_reached(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="completed",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        sample_audio_clip_metric_2 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_2,
        )

        #start

        self.login(self.users[1])

        with self.settings(EVENT_REPLY_DAILY_LIMIT=1):

            data = {}

            request = self.client.post(reverse('list_event_reply_choices_api'), data)

            print_with_function_name(request.content)
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

            print_with_function_name(request.content)
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

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check data

        response_data = get_response_data(request)
        response_data = response_data['data'][0]

        self.assertTrue('event' in response_data and type(response_data['event']) == dict)
        self.assertTrue('originator' in response_data and len(response_data['originator']) == 1)
        self.assertTrue('responder' in response_data and len(response_data['responder']) == 0)
        self.assertTrue('event_reply_queue' in response_data and type(response_data['event_reply_queue']) == dict)

        event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1])
        user_event = UserEvents.objects.get(user=self.users[1], event=event_reply_queue.event)
        originator_audio_clip = AudioClips.objects.get(event=event_reply_queue.event, audio_clip_role__audio_clip_role_name='originator')

        self.assertTrue(response_data['event_reply_queue']['when_locked'] is not None)
        self.assertEqual(response_data['event_reply_queue']['is_replying'], event_reply_queue.is_replying)
        self.assertEqual(response_data['event']['id'], event_reply_queue.event_id)
        self.assertEqual(event_reply_queue.locked_for_user_id, self.users[1].id)
        self.assertEqual(user_event.user_id, self.users[1].id)
        self.assertIsNotNone(user_event.when_excluded_for_reply)
        self.assertEqual(event_reply_queue.event.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(originator_audio_clip.generic_status.generic_status_name, 'ok')
        self.assertNotEqual(originator_audio_clip.user.id, self.users[1].id)
        self.assertEqual(
            AudioClips.objects.filter(
                event=event_reply_queue.event,
                audio_clip_role__audio_clip_role_name='responder',
                generic_status__generic_status_name='ok',
            ).count(),
            0
        )


    def test_list_reply_choices_first_time_has_unlock(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check data

        response_data = get_response_data(request)
        response_data = response_data['data'][0]

        self.assertTrue('event' in response_data and type(response_data['event']) == dict)
        self.assertTrue('originator' in response_data and len(response_data['originator']) == 1)
        self.assertTrue('responder' in response_data and len(response_data['responder']) == 0)
        self.assertTrue('event_reply_queue' in response_data and type(response_data['event_reply_queue']) == dict)

        event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1])
        user_event = UserEvents.objects.get(user=self.users[1], event=event_reply_queue.event)
        originator_audio_clip = AudioClips.objects.get(event=event_reply_queue.event, audio_clip_role__audio_clip_role_name='originator')

        self.assertTrue(response_data['event_reply_queue']['when_locked'] is not None)
        self.assertEqual(response_data['event_reply_queue']['is_replying'], event_reply_queue.is_replying)
        self.assertEqual(response_data['event']['id'], event_reply_queue.event_id)
        self.assertEqual(event_reply_queue.locked_for_user_id, self.users[1].id)
        self.assertEqual(user_event.user_id, self.users[1].id)
        self.assertIsNotNone(user_event.when_excluded_for_reply)
        self.assertEqual(event_reply_queue.event.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(originator_audio_clip.generic_status.generic_status_name, 'ok')
        self.assertNotEqual(originator_audio_clip.user.id, self.users[1].id)
        self.assertEqual(
            AudioClips.objects.filter(
                event=event_reply_queue.event,
                audio_clip_role__audio_clip_role_name='responder',
                generic_status__generic_status_name='ok',
            ).count(),
            0
        )


    def test_list_reply_choices__has_event_but_outdated__no_rows(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        new_when_created = (get_datetime_now() - timedelta(seconds=(settings.EVENT_INCOMPLETE_QUEUE_MAX_AGE_S * 2)))
        new_when_created = new_when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z')

        sample_event_0.when_created = new_when_created
        sample_event_0.save()

        sample_audio_clip_0.when_created = new_when_created
        sample_audio_clip_0.save()

        #start

        self.login(self.users[0])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)
        response_data = response_data['data']

        self.assertEqual(response_data, [])
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(UserEvents.objects.all().count(), 0)


    def test_list_reply_choices__has_own_events__no_rows(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[0])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)
        response_data = response_data['data']

        self.assertEqual(response_data, [])
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(UserEvents.objects.all().count(), 0)


    def test_list_reply_choices__originator_is_blocked__no_rows(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        user_block_0 = self.create_user_block(user_id=self.users[1].id, blocked_user_id=self.users[0].id)

        #start

        #list event

        self.login(self.users[1])

        request = self.client.post(reverse('list_event_reply_choices_api'))

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check data

        response_data = get_response_data(request)
        response_data = response_data['data']

        self.assertEqual(len(response_data), 0)
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(UserEvents.objects.all().count(), 0)


    def test_list_reply_choices__responder_is_blocked__no_rows(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        user_block_0 = self.create_user_block(user_id=self.users[0].id, blocked_user_id=self.users[1].id)

        #start

        #list event

        self.login(self.users[1])

        request = self.client.post(reverse('list_event_reply_choices_api'))

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check data

        response_data = get_response_data(request)
        response_data = response_data['data']

        self.assertEqual(len(response_data), 0)
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(UserEvents.objects.all().count(), 0)


    def test_list_reply_choices__locked_for_someone_else__no_rows(self):

        self.login(self.users[2])

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        self.assertEqual(response_data['data'], [])


    def test_list_reply_choices_has_something_locked__can_return_existing_locked_rows(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )
        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(sample_event_0.id, response_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.filter(event=sample_event_0, user=self.users[1]).count(), 1)
        self.assertEqual(EventReplyQueues.objects.filter(event=sample_event_0, locked_for_user=self.users[1]).count(), 1)

        event_reply_queue = EventReplyQueues.objects.get(event=sample_event_0, locked_for_user=self.users[1])

        self.assertEqual(event_reply_queue.id, sample_event_reply_queue_0.id)
        self.assertEqual(event_reply_queue.when_locked, sample_event_reply_queue_0.when_locked)


    def test_list_reply_choices_has_something_locked__skip_existing_locked_rows(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )
        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        new_event_id = response_data['data'][0]['event']['id']
        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=new_event_id)
        new_event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=new_event_id)

        self.assertEqual(EventReplyQueues.objects.filter(event_id=sample_event_0.id, locked_for_user_id=self.users[1].id).count(), 0)
        self.assertEqual(EventReplyQueues.objects.filter(event_id=new_event_id, locked_for_user_id=self.users[1].id).count(), 1)
        self.assertEqual(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0).count(), 1)
        self.assertEqual(UserEvents.objects.filter(user=self.users[1], event_id=new_event_id).count(), 1)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)
        self.assertNotEqual(new_event_reply_queue.when_locked, sample_event_reply_queue_0.when_locked)


    def test_list_reply_choices_has_something_locked__skip__only_own_rows_allowed(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        #start

        self.login(self.users[2])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())


    def test_list_reply_choices_has_something_locked__can_return_existing_locked_rows__has_expired(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )
        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        new_event_id = response_data['data'][0]['event']['id']
        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=new_event_id)

        self.assertEqual(EventReplyQueues.objects.filter(event_id=sample_event_0.id, locked_for_user_id=self.users[1].id).count(), 0)
        self.assertEqual(EventReplyQueues.objects.filter(event_id=new_event_id, locked_for_user_id=self.users[1].id).count(), 1)
        self.assertEqual(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0).count(), 1)
        self.assertEqual(UserEvents.objects.filter(user=self.users[1], event_id=new_event_id).count(), 1)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)


    def test_list_reply_choices_has_something_locked__skip_existing_locked_rows__has_expired(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )
        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        new_event_id = response_data['data'][0]['event']['id']
        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=new_event_id)

        self.assertEqual(EventReplyQueues.objects.filter(event_id=sample_event_0.id, locked_for_user_id=self.users[1].id).count(), 0)
        self.assertEqual(EventReplyQueues.objects.filter(event_id=new_event_id, locked_for_user_id=self.users[1].id).count(), 1)
        self.assertEqual(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0).count(), 1)
        self.assertEqual(UserEvents.objects.filter(user=self.users[1], event_id=new_event_id).count(), 1)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)


    def test_list_reply_choices_has_something_locked__skip_existing_locked_rows__originator_deleted(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #delete

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 204)

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        new_event_id = response_data['data'][0]['event']['id']
        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=new_event_id)
        new_event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=new_event_id)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertNotEqual(new_event_reply_queue.pk, sample_event_reply_queue_0.id)
        self.assertEqual(EventReplyQueues.objects.filter(event_id=sample_event_0.id, locked_for_user_id=self.users[1].id).count(), 0)
        self.assertEqual(EventReplyQueues.objects.filter(event_id=new_event_id, locked_for_user_id=self.users[1].id).count(), 1)
        self.assertEqual(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0).count(), 1)
        self.assertEqual(UserEvents.objects.filter(user=self.users[1], event_id=new_event_id).count(), 1)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)
        self.assertNotEqual(new_event_reply_queue.when_locked, sample_event_reply_queue_0.when_locked)


    def test_list_reply_choices_has_something_locked__skip_existing_locked_rows__originator_banned(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #ban

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            },
        )

        self.assertEqual(request.status_code, 200)

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        new_event_id = response_data['data'][0]['event']['id']
        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=new_event_id)
        new_event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=new_event_id)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertNotEqual(new_event_reply_queue.pk, sample_event_reply_queue_0.id)
        self.assertEqual(EventReplyQueues.objects.filter(event_id=sample_event_0.id, locked_for_user_id=self.users[1].id).count(), 0)
        self.assertEqual(EventReplyQueues.objects.filter(event_id=new_event_id, locked_for_user_id=self.users[1].id).count(), 1)
        self.assertEqual(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0).count(), 1)
        self.assertEqual(UserEvents.objects.filter(user=self.users[1], event_id=new_event_id).count(), 1)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)
        self.assertNotEqual(new_event_reply_queue.when_locked, sample_event_reply_queue_0.when_locked)


    def test_list_reply_choices_has_something_locked__skip_existing_locked_rows__responder_still_processing(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 400)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())
        self.assertTrue(UserEvents.objects.filter(pk=sample_user_event_0.id).exists())
        self.assertTrue(response_data['has_recording_processing'])

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 400)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())
        self.assertTrue(UserEvents.objects.filter(pk=sample_user_event_0.id).exists())
        self.assertTrue(response_data['has_recording_processing'])


    def test_list_reply_choices__originator_deleted__no_rows(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #delete

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 204)

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check data

        response_data = get_response_data(request)

        self.assertEqual(len(response_data['data']), 0)

        #again

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check data

        response_data = get_response_data(request)

        self.assertEqual(len(response_data['data']), 0)


    def test_list_reply_choices__originator_banned__no_rows(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
            is_banned=True,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #ban

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            },
        )

        self.assertEqual(request.status_code, 200)

        #start

        self.login(self.users[1])

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check data

        response_data = get_response_data(request)

        self.assertEqual(len(response_data['data']), 0)

        #again

        data = {'unlock_all_locked_events': True}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check data

        response_data = get_response_data(request)

        self.assertEqual(len(response_data['data']), 0)


    def test_start_replies_ok(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        old_when_locked = sample_event_reply_queue_0.when_locked

        sample_event_reply_queue_0.refresh_from_db()

        self.assertTrue(sample_event_reply_queue_0.is_replying)
        self.assertEqual(response_data['data']['event_id'], sample_event_reply_queue_0.event_id)
        self.assertEqual(
            datetime.strptime(
                response_data['data']['when_locked'], "%Y-%m-%dT%H:%M:%S.%fZ"
            ).replace(tzinfo=ZoneInfo('UTC')),
            sample_event_reply_queue_0.when_locked
        )
        self.assertNotEqual(old_when_locked, sample_event_reply_queue_0.when_locked)
        self.assertEqual(
            response_data['data']['is_replying'], sample_event_reply_queue_0.is_replying
        )


    def test_start_replies_with_missing_args(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=sample_event_0.id)

        self.assertFalse(event_reply_queue.is_replying)


    def test_start_replies_with_faulty_args(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=sample_event_0.id)

        self.assertFalse(event_reply_queue.is_replying)


    def test_start_replies_but_never_queued(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        print_with_function_name(request.content)

        self.assertEqual(request.status_code, 404)


    def test_start_replies__expired(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertFalse(response_data['can_retry'])
        self.assertEqual(
            EventReplyQueues.objects.filter(
                event_id=sample_event_0.id,
                locked_for_user_id=self.users[1].id,
                is_replying=False,
            ).count(),
            0
        )
        self.assertEqual(
            UserEvents.objects.filter(
                user=self.users[1],
                event_id=sample_event_0.id,
                when_excluded_for_reply__isnull=False
            ).count(),
            1
        )


    def test_start_replies__originator_is_deleted(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
            is_banned=False,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        #delete

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 204)

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 404)

        #check

        response_data = get_response_data(request)

        self.assertFalse(response_data['can_retry'])
        self.assertEqual(
            EventReplyQueues.objects.filter(
                event_id=sample_event_0.id,
                locked_for_user_id=self.users[1].id,
            ).count(),
            0
        )
        self.assertEqual(
            UserEvents.objects.filter(
                user=self.users[1],
                event_id=sample_event_0.id,
                when_excluded_for_reply__isnull=False
            ).count(),
            1
        )


    def test_start_replies__originator_is_banned(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
            is_banned=False,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        #ban

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            },
        )

        self.assertEqual(request.status_code, 200)

        #start

        self.login(self.users[1])

        data = {'event_id': sample_event_0.id}

        request = self.client.post(reverse('start_replies_api'), data)

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 404)

        #check

        response_data = get_response_data(request)

        self.assertFalse(response_data['can_retry'])
        self.assertEqual(
            EventReplyQueues.objects.filter(
                event_id=sample_event_0.id,
                locked_for_user_id=self.users[1].id,
            ).count(),
            0
        )
        self.assertEqual(
            UserEvents.objects.filter(
                user=self.users[1],
                event_id=sample_event_0.id,
                when_excluded_for_reply__isnull=False
            ).count(),
            1
        )


    def test_start_replies__only_own_rows_allowed(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_event_reply_queue_0.refresh_from_db()

        self.assertEqual(sample_event_reply_queue_0.is_replying, False)
        self.assertEqual(
            UserEvents.objects.filter(
                user=self.users[2],
                event_id=sample_event_0.id,
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 201)

        #check

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('event_id' in response_data)
        self.assertTrue('audio_clip_id' in response_data)

        self.assertTrue('key' in json.loads(response_data['upload_fields']))

        sample_event_0.refresh_from_db()
        audio_clip = AudioClips.objects.select_related('generic_status',).get(
            user_id=self.users[1],
            generic_status__generic_status_name='processing_pending',
            audio_clip_role__audio_clip_role_name='responder',
            event_id=sample_event_0.id,
        )

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
        self.assertTrue(
            EventReplyQueues.objects.filter(
                pk=sample_event_reply_queue_0.id
            ).exists()
        )
        self.assertEqual(response_data['audio_clip_id'], audio_clip.id)
        self.assertTrue(AudioClipMetrics.objects.filter(audio_clip_id=audio_clip.id).exists())


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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        print_with_function_name(request.content)
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        print_with_function_name(request.content)
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 205)

        #check

        self.assertEqual(EventReplyQueues.objects.all().count(), 0)


    def test_create_replies__upload__originator_is_deleted(self):

        #prepare data

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        #delete

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 204)

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 404)

        #check

        self.assertEqual(EventReplyQueues.objects.all().count(), 0)


    def test_create_replies__upload__originator_is_banned(self):

        #prepare data

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        #ban

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        self.assertEqual(request.status_code, 200)

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS[0],
        }

        request = self.client.post(reverse('create_replies_upload_api'), data)

        print_with_function_name(request.content)
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('key' in json.loads(response_data['upload_fields']))
        self.assertFalse('event_id' in response_data)
        self.assertFalse('audio_clip_id' in response_data)


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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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

        sample_audio_clip_metric_2 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_2,
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

        sample_audio_clip_metric_3 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_3,
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 404)


    def test_create_replies__regenerate_upload_url__originator_is_deleted(self):

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #delete

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 204)

        #proceed

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('key' in json.loads(response_data['upload_fields']))
        self.assertFalse('event_id' in response_data)
        self.assertFalse('audio_clip_id' in response_data)


    def test_create_replies__regenerate_upload_url__originator_is_banned(self):

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #ban

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            },
        )

        self.assertEqual(request.status_code, 200)

        #proceed

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('key' in json.loads(response_data['upload_fields']))
        self.assertFalse('event_id' in response_data)
        self.assertFalse('audio_clip_id' in response_data)


    def test_create_replies__regenerate_upload_url__own_audio_clip_is_deleted(self):

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #delete, should fail

        self.login(self.users[1])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_1.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 400)

        #proceed

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('key' in json.loads(response_data['upload_fields']))
        self.assertFalse('event_id' in response_data)
        self.assertFalse('audio_clip_id' in response_data)


    def test_create_replies__regenerate_upload_url__own_audio_clip_is_banned(self):

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #ban, should fail

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        print(request.content)
        self.assertEqual(request.status_code, 400)

        #proceed

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        response_data = get_response_data(request)

        self.assertTrue('upload_url' in response_data)
        self.assertTrue('upload_fields' in response_data)
        self.assertTrue('key' in json.loads(response_data['upload_fields']))
        self.assertFalse('event_id' in response_data)
        self.assertFalse('audio_clip_id' in response_data)


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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #proceed

        data = {}

        request = self.client.post(reverse('create_replies_regenerate_upload_url_api'), data)

        print_with_function_name(request.content)
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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


    def test_create_replies__process__processing(self):

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_1.event,
                audio_clip=sample_audio_clip_1,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['status'] = sample_audio_clip_1.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 409)
        self.assertTrue("attempts_left" in response_data)
        self.assertEqual(response_data['status'], 'processing')
        self.assertEqual(
            response_data['attempts_left'],
            settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        )
        self.assertTrue(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )


    def test_create_replies__process__processing__queue_expired(self):

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        sample_event_reply_queue_0.when_locked = get_datetime_now() - timedelta(seconds=settings.EVENT_REPLY_MAX_DURATION_S + 2)
        sample_event_reply_queue_0.save()

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_1.event,
                audio_clip=sample_audio_clip_1,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['status'] = sample_audio_clip_1.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 409)
        self.assertTrue("attempts_left" in response_data)
        self.assertEqual(response_data['status'], 'processing')
        self.assertEqual(
            response_data['attempts_left'],
            settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        )
        self.assertTrue(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )


    def test_create_replies__process__queue_expired(self):

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_generic_status_generic_status_name='processing_pending',
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        sample_event_reply_queue_0.when_locked = get_datetime_now() - timedelta(seconds=settings.EVENT_REPLY_MAX_DURATION_S + 2)
        sample_event_reply_queue_0.save()

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 404)

        sample_audio_clip_1.refresh_from_db()

        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertFalse(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertFalse(str(sample_audio_clip_1.id) in target_cache['processings'])


    def test_create_replies__process__queue_ok__event_unavailable(self):

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        sample_user_event_0 = self.create_user_event(
            self.users[1].id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        generic_status_deleted = GenericStatuses.objects.get(generic_status_name='deleted')

        sample_event_0.generic_status = generic_status_deleted
        sample_event_0.save()
        sample_audio_clip_0.generic_status = generic_status_deleted
        sample_audio_clip_0.save()

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
            audio_clip_generic_status_generic_status_name='processing_pending',
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 404)

        sample_audio_clip_1.refresh_from_db()

        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertFalse(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertFalse(str(sample_audio_clip_1.id) in target_cache['processings'])


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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #no cache

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        self.assertEqual(request.status_code, 404)


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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_generic_status_generic_status_name='processing_pending',
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 404)


    def test_create_replies__process__processing__originator_is_deleted(self):

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        #delete

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 204)

        #processing should fail

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 404)
        self.assertFalse(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )


    def test_create_replies__process__processing__originator_is_banned(self):

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_1.event,
                audio_clip=sample_audio_clip_1,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['status'] = sample_audio_clip_1.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #ban

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            },
        )

        self.assertEqual(request.status_code, 200)

        #processing should fail

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 404)
        self.assertFalse(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )
        self.assertFalse(str(sample_audio_clip_1.id) in cache.get(target_cache_key, None))


    def test_create_replies__process__processing__attempt_deletion_for_responder(self):

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_1.event,
                audio_clip=sample_audio_clip_1,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['status'] = sample_audio_clip_1.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #delete, should fail

        self.login(self.users[1])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_1.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 400)

        #processing should still be allowed

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 409)
        self.assertTrue("attempts_left" in response_data)
        self.assertEqual(response_data['status'], 'processing')
        self.assertEqual(
            response_data['attempts_left'],
            settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        )
        self.assertTrue(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )


    def test_create_replies__process__processing__attempt_ban_for_responder(self):

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        #ban, should fail

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            },
        )

        self.assertEqual(request.status_code, 400)

        #processing should still be allowed

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 409)
        self.assertTrue("attempts_left" in response_data)
        self.assertEqual(response_data['status'], 'processing')
        self.assertEqual(
            response_data['attempts_left'],
            settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS
        )
        self.assertTrue(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )


    def test_create_replies__process__processing_failed__originator_is_deleted(self):

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_generic_status_generic_status_name='processing_failed',
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        #delete

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 204)

        #processing should fail

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 404)
        self.assertFalse(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )


    def test_create_replies__process__processing_failed__originator_is_banned(self):

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_generic_status_generic_status_name='processing_failed',
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #ban

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            },
        )

        self.assertEqual(request.status_code, 200)

        #processing should fail

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }

        request = self.client.post(reverse('create_replies_process_api'), data)

        response_data = get_response_data(request)

        self.assertEqual(request.status_code, 404)
        self.assertFalse(
            EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists()
        )


    def test_create_replies__process__processing_failed__attempt_deletion_for_responder(self):

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_generic_status_generic_status_name='processing_failed',
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_1.event,
                audio_clip=sample_audio_clip_1,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['status'] = sample_audio_clip_1.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #delete, should fail

        self.login(self.users[1])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_1.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 400)

        #no change

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        target_cache = cache.get(target_cache_key, None)

        sample_event_0.generic_status.generic_status_name = 'incomplete'
        sample_audio_clip_0.generic_status.geneic_status_name = 'ok'
        sample_audio_clip_1.generic_status.geneic_status_name = 'processing_failed'
        self.assertIsNotNone(CreateAudioClips.get_processing_object_from_processing_cache(target_cache, sample_audio_clip_1.id))


    def test_create_replies__process__processing_failed__attempt_ban_for_responder(self):

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_generic_status_generic_status_name='processing_failed',
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_1.event,
                audio_clip=sample_audio_clip_1,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['status'] = sample_audio_clip_1.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #ban, should fail

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            },
        )

        self.assertEqual(request.status_code, 400)

        #no change

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        target_cache = cache.get(target_cache_key, None)

        sample_event_0.generic_status.generic_status_name = 'incomplete'
        sample_audio_clip_0.generic_status.geneic_status_name = 'ok'
        sample_audio_clip_1.generic_status.geneic_status_name = 'processing_failed'
        self.assertIsNotNone(CreateAudioClips.get_processing_object_from_processing_cache(target_cache, sample_audio_clip_1.id))


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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())


    def test_cancel_reply_with_missing_args(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)


    def test_cancel_reply_with_faulty_args(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)


    def test_cancel_reply_but_never_queued_for_it(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_with_function_name(request.content)


    def test_cancel_reply_locked_but_not_replying(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertFalse(
            EventReplyQueues.objects.filter(
                locked_for_user=self.users[1],
                event_id=sample_event_0.id
            ).exists()
        )
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())


    def test_cancel_reply__only_own_rows_allowed(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertTrue(EventReplyQueues.objects.filter(locked_for_user=self.users[2], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[2], event_id=sample_event_0.id).exists())


    def test_cancel_reply__event_is_deleted(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        #delete

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 204)

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertFalse(response_data['can_retry'])


    def test_cancel_reply__event_is_banned(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        #ban

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            },
        )

        self.assertEqual(request.status_code, 200)

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertFalse(response_data['can_retry'])


    def test_cancel_reply__processing(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_1.event,
                audio_clip=sample_audio_clip_1,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['status'] = sample_audio_clip_1.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_with_function_name(request.content)

        #check

        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()

        response_data = get_response_data(request)

        self.assertTrue(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 2)
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'processing')
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertTrue(response_data['has_recording_processing'])

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertEqual(len(target_cache['processings']), 1)


    def test_cancel_reply__processing_failed__ok(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
            audio_clip_generic_status_generic_status_name='processing_failed',
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_1.event,
                audio_clip=sample_audio_clip_1,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['status'] = sample_audio_clip_1.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        #start

        self.login(self.users[1])

        data = {
            'event_id': sample_event_0.id,
        }

        request = self.client.post(reverse('cancel_replies_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()

        response_data = get_response_data(request)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 2)
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertFalse('has_recording_processing' in response_data)

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertEqual(len(target_cache['processings']), 0)


    def test_audio_clip_report__ok(self):

        #prepare

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertIsNone(audio_clip_report.last_evaluated)


    def test_audio_clip_report__not_ok(self):

        #prepare

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 404)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(AudioClipReports.objects.all().count(), 0)


    def test_audio_clip_report__missing_args(self):

        #prepare

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[1])

        data = {
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 400)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 0)


    def test_audio_clip_report__faulty_args(self):

        #prepare

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[1])

        data = {
            'yolo': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 400)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 0)


    def test_audio_clip_report__not_found(self):

        #prepare

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': 9999999
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 404)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 0)


    def test_audio_clip_report__already_reported_before(self):

        #prepare

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertLess(sample_audio_clip_report_0.last_reported, audio_clip_report.last_reported)


    def test_audio_clip_report__already_banned(self):

        #prepare

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
            audio_clip_is_banned=True,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        self.assertEqual(request.status_code, 400)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertIsNotNone(audio_clip_report.last_evaluated)


    def test_audio_clip_report__self_ok(self):

        #prepare

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[0])

        data = {
            'audio_clip_id': sample_audio_clip_0.id
        }

        request = self.client.post(reverse('create_audio_clip_reports_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.filter(user=self.users[1], blocked_user=self.users[0]).count(), 1)
        self.assertIsNone(response_data.get('when_last_action_s', None))


    def test_user_block__missing_args(self):

        self.login(self.users[1])

        #start

        data = {
            'username': self.users[0].username,
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 400)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.filter(user=self.users[1], blocked_user=self.users[0]).count(), 0)

        #start

        data = {
            'to_block': True,
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 400)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.filter(user=self.users[1], blocked_user=self.users[0]).count(), 0)


    def test_user_block__faulty_args(self):

        self.login(self.users[1])

        #start

        data = {
            'username': self.users[0].username,
            'to_block': '',
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        #200 because bool defaults to False when not passed
        self.assertEqual(request.status_code, 400)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.filter(user=self.users[1], blocked_user=self.users[0]).count(), 0)

        #start

        data = {
            'username': 200,
            'to_block': True,
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        #200 because bool defaults to False when not passed
        self.assertEqual(request.status_code, 404)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.filter(user=self.users[1], blocked_user=self.users[0]).count(), 0)


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
        print_with_function_name(request.content)

        #check

        self.assertEqual(UserBlocks.objects.filter(user=self.users[0], blocked_user=self.users[1]).count(), 1)
        self.assertEqual(UserBlocks.objects.filter(user=self.users[0], blocked_user=self.users[2]).count(), 1)


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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.filter(user=self.users[0], blocked_user=self.users[1]).count(), 1)


    def test_user_block__block_themselves(self):

        self.login(self.users[0])

        data = {
            'username': self.users[0].username,
            'to_block': True
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 400)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.filter(user=self.users[0], blocked_user=self.users[0]).count(), 0)


    def test_user_block__user_does_not_exist(self):


        self.login(self.users[1])

        data = {
            'username': self.non_existent_username,
            'to_block': True
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 404)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.filter(user=self.users[1], blocked_user__username=self.non_existent_username).count(), 0)


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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.filter(user=self.users[1], blocked_user=self.users[0]).count(), 0)

        #refetch using when_last_action_s

        when_last_action_s = cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(self.users[1].id), None)

        request = self.client.get(reverse('user_blocks_api'), {'when_last_action_s': when_last_action_s})

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(len(response_data['data']), 0)
        self.assertEqual(response_data['is_up_to_date'], True)


    def test_user_block__block_banned_user_ok(self):

        self.login(self.users[0])

        data = {
            'username': self.banned_users[1].username,
            'to_block': True
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(len(response_data['data']), 2)


    def test_user_block__cache_behaviour__no_db_rows__no_cache(self):

        self.login(self.users[0])

        #cache does not exist, API ensures it exists

        request = self.client.get(reverse('user_blocks_api'))

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)
        when_last_action_s = cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None)

        self.assertEqual(len(response_data['data']), 0)
        self.assertGreater(response_data['when_last_action_s'], 0)
        self.assertIsNotNone(when_last_action_s)

        #block yourself
        #expect cache to stay the same

        #must delay, else test runs too quickly and we get same when_last_action_s
        time.sleep(2)

        request = self.client.post(
            reverse('user_blocks_api'),
            data={
                'username': self.users[0].username,
                'to_block': True
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 400)

        #check

        response_data = get_response_data(request)

        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertEqual(when_last_action_s, cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))

        #block someone
        #expect cache to be updated

        time.sleep(2)

        request = self.client.post(
            reverse('user_blocks_api'),
            data={
                'username': self.users[1].username,
                'to_block': True
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertLess(when_last_action_s, cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))

        #unblock someone
        #expect cache to be updated

        when_last_action_s = cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None)

        time.sleep(2)

        request = self.client.post(
            reverse('user_blocks_api'),
            data={
                'username': self.users[1].username,
                'to_block': False
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertLess(when_last_action_s, cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))

        #do GET

        when_last_action_s = cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None)

        request = self.client.get(reverse('user_blocks_api'), data={'when_last_action_s': when_last_action_s})

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        self.assertTrue(response_data['is_up_to_date'])
        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertEqual(when_last_action_s, cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))


    def test_user_block__cache_behaviour__has_db_rows__no_cache(self):

        self.login(self.users[0])

        UserBlocks.objects.bulk_create([
            UserBlocks(user=self.users[0], blocked_user=self.users[1]),
        ])

        self.login(self.users[0])

        #cache does not exist, API ensures it exists

        request = self.client.get(reverse('user_blocks_api'))

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)
        when_last_action_s = cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None)

        self.assertEqual(len(response_data['data']), 1)
        self.assertGreater(response_data['when_last_action_s'], 0)
        self.assertIsNotNone(when_last_action_s)

        #block yourself
        #expect cache to stay the same

        #must delay, else test runs too quickly and we get same when_last_action_s
        time.sleep(2)

        request = self.client.post(
            reverse('user_blocks_api'),
            data={
                'username': self.users[0].username,
                'to_block': True
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 400)

        #check

        response_data = get_response_data(request)

        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertEqual(when_last_action_s, cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))

        #block someone
        #expect cache to be updated

        time.sleep(2)

        request = self.client.post(
            reverse('user_blocks_api'),
            data={
                'username': self.users[1].username,
                'to_block': True
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertLess(when_last_action_s, cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))

        #unblock someone
        #expect cache to be updated

        when_last_action_s = cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None)

        time.sleep(2)

        request = self.client.post(
            reverse('user_blocks_api'),
            data={
                'username': self.users[1].username,
                'to_block': False
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertLess(when_last_action_s, cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))

        #do GET

        when_last_action_s = cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None)

        request = self.client.get(reverse('user_blocks_api'), data={'when_last_action_s': when_last_action_s})

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        self.assertTrue(response_data['is_up_to_date'])
        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertEqual(when_last_action_s, cache.get(UserBlocksAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))


    def test_user_block__get_no_rows(self):

        self.login(self.users[0])

        request = self.client.get(reverse('user_blocks_api'))

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserBlocks.objects.filter(user=self.users[0], blocked_user=self.users[1]).count(), 1)
        self.assertEqual(UserBlocks.objects.filter(user=self.users[0], blocked_user=self.banned_users[1]).count(), 0)


    def test_user_block__response_size_at_limit(self):

        #test results requiring only names of 1000 users
            #serializer (66900 bytes)
            #pure list [] (18900 bytes)

        user_blocks = []
        test_user_blocks_row_count = 1000

        for x in range(0, test_user_blocks_row_count):

            current_user = get_user_model().objects.create_user(
                username='userBlockTest'+str(x),
                email='userblocktest'+str(x)+'@gmail.com',
            )

            current_user.is_active = True
            current_user.save()

            user_blocks.append(UserBlocks(user=self.users[0], blocked_user=current_user))

        UserBlocks.objects.bulk_create(user_blocks)

        self.login(self.users[0])

        with self.settings(USER_BLOCKS_LIMIT=test_user_blocks_row_count):

            request = self.client.get(reverse('user_blocks_api'))

        self.assertEqual(request.status_code, 200)
        # print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertTrue(request.has_header('Content-Length'))
        self.assertEqual(len(response_data['data']), test_user_blocks_row_count)

        print(request.headers['Content-Length'])
        print(response_data['data'][0])

        with self.assertNumQueries(1):

            result = UserBlocks.objects.select_related('blocked_user').filter(
                user=self.users[0],
            ).order_by('when_created').values_list('blocked_user__username')

            print(len(result))
            print(result[0][0])


    def test_audio_clip_like_dislike__missing_args(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[1])

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        #bool defaults to False by serializer
        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        data = {
            'is_liked': True,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 400)
        print_with_function_name(request.content)


    def test_audio_clip_like_dislike__faulty_args(self):


        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        print_with_function_name(request.content)

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': 2,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 400)
        print_with_function_name(request.content)

        data = {
            'audio_clip_id': 999,
            'is_liked': True,
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 404)
        print_with_function_name(request.content)


    def test_audio_clip_like_dislike__create_and_delete__like(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[1])

        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_metric_0.like_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 1)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)

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
        sample_audio_clip_metric_0.refresh_from_db()
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)


    def test_audio_clip_like_dislike__create_and_delete__dislike(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[1])

        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': False
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 1)

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
        sample_audio_clip_metric_0.refresh_from_db()
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)


    def test_audio_clip_like_dislike__random_audio_clip_like_dislike_chaining(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #start

        self.login(self.users[1])

        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_metric_0.like_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 1)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertTrue(audio_clip_like_dislike.is_liked)

        #switch

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': False
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 1)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertFalse(audio_clip_like_dislike.is_liked)

        #switch again

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_metric_0.like_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 1)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)

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
        sample_audio_clip_metric_0.refresh_from_db()
        self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[1]).exists())

        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)

        #like

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(user=self.users[1])

        self.assertEqual(sample_audio_clip_metric_0.like_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 1)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)

        self.assertEqual(audio_clip_like_dislike.audio_clip_id, sample_audio_clip_0.id)
        self.assertTrue(audio_clip_like_dislike.is_liked)


    def test_audio_clip_like_dislike__deleted_audio_clip__not_allowed(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="deleted",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )
        sample_audio_clip_0.generic_status = GenericStatuses.objects.get(generic_status_name='deleted')
        sample_audio_clip_0.save()
        sample_audio_clip_1.generic_status = GenericStatuses.objects.get(generic_status_name='deleted')
        sample_audio_clip_1.save()

        #first we log in as originator, then responder, then as an unrelated user

        all_relevant_users = [
            self.users[0],
            self.users[1],
            self.users[2]
        ]

        for current_user in all_relevant_users:

            self.login(current_user)

            #originator audio_clip

            data = {
                'audio_clip_id': sample_audio_clip_0.id,
                'is_liked': True
            }

            request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

            self.assertEqual(request.status_code, 400)
            print_with_function_name(request.content)

            #check

            response_data = get_response_data(request)

            sample_audio_clip_0.refresh_from_db()
            sample_audio_clip_metric_0.refresh_from_db()

            self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
            self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
            self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
            self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[0], audio_clip=sample_audio_clip_0).exists())

            #responder audio_clip

            data = {
                'audio_clip_id': sample_audio_clip_1.id,
                'is_liked': True
            }

            request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

            self.assertEqual(request.status_code, 400)
            print_with_function_name(request.content)

            #check

            response_data = get_response_data(request)

            sample_audio_clip_1.refresh_from_db()
            sample_audio_clip_metric_1.refresh_from_db()

            self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
            self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
            self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
            self.assertFalse(AudioClipLikesDislikes.objects.filter(user=self.users[0], audio_clip=sample_audio_clip_1).exists())


    def test_audio_clip_like_dislike__duplicate_delete__duplicate_new_row(self):

        #prepare data

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            like_count=1,
            dislike_count=0,
            like_ratio=1,
        )

        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
            user=self.users[0],
            audio_clip=sample_audio_clip_0,
            is_liked=True,
        )

        #like again

        self.login(self.users[0])

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': True
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_metric_0.refresh_from_db()

        self.assertEqual(sample_audio_clip_metric_0.like_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 1)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_0.id).count(), 1)

        #delete like

        self.login(self.users[0])

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': json.dumps(None),
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_metric_0.refresh_from_db()

        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_0.id).count(), 0)

        #delete like again

        self.login(self.users[0])

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
            'is_liked': json.dumps(None),
        }

        request = self.client.post(reverse('audio_clip_likes_dislikes_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        sample_audio_clip_metric_0.refresh_from_db()

        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(pk=sample_audio_clip_like_dislike_0.id).count(), 0)


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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_event_0,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

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
        self.assertEqual(
            response_data['data']['processings'][str(sample_audio_clip_0.id)]['status'],
            sample_audio_clip_0.generic_status.generic_status_name
        )


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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_event_0,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

        cache.set(target_cache_key, target_cache)

        request = self.client.get(
            reverse(
                'list_audio_clip_processings_api',
            )
        )

        response_data = get_response_data(request)
        self.assertEqual(len(response_data['data']['processings']), 0)


    def test_list_audio_clip_processing__cache_sync_retriggered(self):

        self.login(self.users[0])

        for loop_count, generic_status_name in enumerate(['processing_pending', 'processing', 'processing_failed']):

            sample_event_0 = EventsFactory(
                event_created_by=self.users[0],
                event_generic_status_generic_status_name='processing',
            )

            sample_audio_clip_0 = AudioClipsFactory(
                audio_clip_user=self.users[0],
                audio_clip_audio_clip_role_audio_clip_role_name='originator',
                audio_clip_event=sample_event_0,
                audio_clip_generic_status_generic_status_name=generic_status_name,
            )
            sample_audio_clip_metric_0 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_0,
            )

            request = self.client.get(
                reverse(
                    'list_audio_clip_processings_api',
                )
            )

            #expect default cache to be auto-created

            response_data = get_response_data(request)
            self.assertEqual(len(response_data['data']['processings']), loop_count+1)
            self.assertTrue(str(sample_audio_clip_0.id) in response_data['data']['processings'])

            cache.delete(CreateAudioClips.determine_processing_cache_key(self.users[0].id))


    def test_list_audio_clip_processing__cache_sync_not_triggered(self):

        target_user = self.create_user()

        self.login(target_user)

        for loop_count, generic_status_name in enumerate(['processing_pending', 'processing', 'processing_failed']):

            sample_event_0 = EventsFactory(
                event_created_by=target_user,
                event_generic_status_generic_status_name='processing',
            )

            sample_audio_clip_0 = AudioClipsFactory(
                audio_clip_user=target_user,
                audio_clip_audio_clip_role_audio_clip_role_name='originator',
                audio_clip_event=sample_event_0,
                audio_clip_generic_status_generic_status_name=generic_status_name,
            )
            sample_audio_clip_metric_0 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_0,
            )

            request = self.client.get(
                reverse(
                    'list_audio_clip_processings_api',
                )
            )

            #since only triggering sync once, cache will only have first processing

            response_data = get_response_data(request)
            self.assertEqual(len(response_data['data']['processings']), 1)

            if loop_count == 0:

                self.assertTrue(str(sample_audio_clip_0.id) in response_data['data']['processings'])

            else:

                self.assertFalse(str(sample_audio_clip_0.id) in response_data['data']['processings'])


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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_event_0,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

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
        self.assertTrue('attempts_left' in response_data)
        self.assertEqual(response_data['status'], sample_audio_clip_0.generic_status.generic_status_name)
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
            audio_clip_generic_status_generic_status_name='processing_failed',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_event_0,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

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
        self.assertEqual(response_data['status'], sample_audio_clip_0.generic_status.generic_status_name)
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_event_0,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
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

        for generic_status_name in ['processing_pending', 'processing', 'processing_failed']:

            sample_event_0 = EventsFactory(
                event_created_by = self.users[0],
                event_generic_status_generic_status_name = 'processing',
            )

            sample_audio_clip_0 = AudioClipsFactory(
                audio_clip_user=self.users[0],
                audio_clip_audio_clip_role_audio_clip_role_name='originator',
                audio_clip_event=sample_event_0,
                audio_clip_generic_status_generic_status_name=generic_status_name,
            )
            sample_audio_clip_metric_0 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_0,
            )

            #set cache

            target_cache_key = CreateAudioClips.determine_processing_cache_key(
                user_id=self.users[0].id,
            )

            target_cache = CreateAudioClips.get_default_processing_cache_per_user()

            target_cache['processings'].update({
                str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                    event=sample_event_0,
                    audio_clip=sample_audio_clip_0,
                ),
            })

            target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] -= 1
            target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

            cache.set(target_cache_key, target_cache)

            #proceed

            data = {
                'audio_clip_id': sample_audio_clip_0.id,
            }

            request = self.client.post(reverse('delete_audio_clip_processings_api'), data)

            sample_event_0.refresh_from_db()
            sample_audio_clip_0.refresh_from_db()

            if generic_status_name == 'processing':

                self.assertTrue(request.status_code, 409)

                self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
                self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_0.id).exists())
                self.assertEqual(sample_event_0.generic_status.generic_status_name, 'processing')
                self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'processing')

                target_cache = cache.get(target_cache_key)

                self.assertIsNotNone(target_cache['processings'].get(str(sample_audio_clip_0.id), None))

            else:

                self.assertTrue(request.status_code, 200)

                sample_event_0.refresh_from_db()
                sample_audio_clip_0.refresh_from_db()

                self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
                self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_0.id).exists())
                self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
                self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                event=sample_event_0,
                audio_clip=sample_audio_clip_0,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

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


    def test_originator__delete_audio_clip_processing__already_deleted(self):

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
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[0].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

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

        for generic_status_name in ['processing_pending', 'processing', 'processing_failed']:

            sample_event_0 = EventsFactory(
                event_created_by = self.users[0],
                event_generic_status_generic_status_name = 'incomplete',
            )

            sample_audio_clip_0 = AudioClipsFactory(
                audio_clip_user=self.users[0],
                audio_clip_audio_clip_role_audio_clip_role_name='originator',
                audio_clip_event=sample_event_0,
            )

            sample_audio_clip_metric_0 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_0,
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
                audio_clip_generic_status_generic_status_name=generic_status_name,
            )

            sample_audio_clip_metric_1 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_1,
            )

            #set cache

            target_cache_key = CreateAudioClips.determine_processing_cache_key(
                user_id=self.users[1].id,
            )

            target_cache = CreateAudioClips.get_default_processing_cache_per_user()

            target_cache['processings'].update({
                str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_object(
                    event=sample_audio_clip_1.event,
                    audio_clip=sample_audio_clip_1,
                ),
            })

            target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] -= 1
            target_cache['processings'][str(sample_audio_clip_1.id)]['status'] = sample_audio_clip_1.generic_status.generic_status_name

            cache.set(target_cache_key, target_cache)

            #proceed

            data = {
                'audio_clip_id': sample_audio_clip_1.id,
            }

            request = self.client.post(reverse('delete_audio_clip_processings_api'), data)

            sample_event_0.refresh_from_db()
            sample_audio_clip_0.refresh_from_db()
            sample_audio_clip_1.refresh_from_db()

            if generic_status_name == 'processing':

                self.assertTrue(request.status_code, 409)

                self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
                self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_1.id).exists())
                self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
                self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'processing')

                target_cache = cache.get(target_cache_key)

                self.assertIsNotNone(target_cache['processings'].get(str(sample_audio_clip_1.id), None))

            else:

                self.assertTrue(request.status_code, 200)

                self.assertTrue(Events.objects.filter(pk=sample_event_0.id).exists())
                self.assertTrue(AudioClips.objects.filter(pk=sample_audio_clip_1.id).exists())
                self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
                self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

        target_cache['processings'].update({
            str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_object(
                event=sample_audio_clip_1.event,
                audio_clip=sample_audio_clip_1,
            ),
        })

        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] -= 1
        target_cache['processings'][str(sample_audio_clip_1.id)]['status'] = sample_audio_clip_1.generic_status.generic_status_name

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

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
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

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )
        #set cache

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=self.users[1].id,
        )

        target_cache = CreateAudioClips.get_default_processing_cache_per_user()

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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.all().count(), 1)
        self.assertIsNone(response_data.get('when_last_action_s', None))


    def test_user_following__already_following(self):

        UserFollows.objects.create(user=self.users[0], followed_user=self.users[1])

        self.login(self.users[0])

        data = {
            'username': self.users[1].username,
            'to_follow': True
        }

        request = self.client.post(reverse('user_follows_api'), data)

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.all().count(), 0)


    def test_user_following__get_no_rows(self):

        self.login(self.users[0])

        request = self.client.get(reverse('user_follows_api'))

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

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
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertEqual(UserFollows.objects.filter(followed_user=self.banned_users[2]).count(), 0)
        self.assertEqual(UserFollows.objects.all().count(), 1)


    def test_user_following__response_size_at_limit(self):

        #test results requiring only names of 1000 users
            #serializer (66900 bytes)
            #pure list [] (18900 bytes)

        user_follows = []
        test_user_follows_row_count = 1000

        for x in range(0, test_user_follows_row_count):

            current_user = get_user_model().objects.create_user(
                username='userFollowTest'+str(x),
                email='userfollowtest'+str(x)+'@gmail.com',
            )

            current_user.is_active = True
            current_user.save()

            user_follows.append(UserFollows(user=self.users[0], followed_user=current_user))

        UserFollows.objects.bulk_create(user_follows)

        self.login(self.users[0])

        with self.settings(USER_FOLLOWS_LIMIT=test_user_follows_row_count):

            request = self.client.get(reverse('user_follows_api'))

        self.assertEqual(request.status_code, 200)
        # print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)

        self.assertTrue(request.has_header('Content-Length'))
        self.assertEqual(len(response_data['data']), test_user_follows_row_count)

        print(request.headers['Content-Length'])
        print(response_data['data'][0])

        with self.assertNumQueries(1):

            result = UserFollows.objects.select_related('followed_user').filter(
                user=self.users[0]
            ).order_by(
                'when_created'
            ).values_list(
                'followed_user__username'
            )

            print(len(result))
            print(result[0][0])


    def test_user_following__cache_behaviour__no_db_rows__no_cache(self):

        self.login(self.users[0])

        #cache does not exist, API ensures it exists

        request = self.client.get(reverse('user_follows_api'))

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)
        when_last_action_s = cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None)

        self.assertEqual(len(response_data['data']), 0)
        self.assertGreater(response_data['when_last_action_s'], 0)
        self.assertIsNotNone(when_last_action_s)

        #follow yourself
        #expect cache to stay the same

        #must delay, else test runs too quickly and we get same when_last_action_s
        time.sleep(2)

        request = self.client.post(
            reverse('user_follows_api'),
            data={
                'username': self.users[0].username,
                'to_follow': True
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 400)

        #check

        response_data = get_response_data(request)

        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertEqual(when_last_action_s, cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))

        #follow someone
        #expect cache to be updated

        time.sleep(2)

        request = self.client.post(
            reverse('user_follows_api'),
            data={
                'username': self.users[1].username,
                'to_follow': True
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertLess(when_last_action_s, cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))

        #unfollow someone
        #expect cache to be updated

        when_last_action_s = cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None)

        time.sleep(2)

        request = self.client.post(
            reverse('user_follows_api'),
            data={
                'username': self.users[1].username,
                'to_follow': False
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertLess(when_last_action_s, cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))

        #do GET

        when_last_action_s = cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None)

        request = self.client.get(reverse('user_follows_api'), data={'when_last_action_s': when_last_action_s})

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        self.assertTrue(response_data['is_up_to_date'])
        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertEqual(when_last_action_s, cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))


    def test_user_following__cache_behaviour__has_db_rows__no_cache(self):

        self.login(self.users[0])

        UserFollows.objects.bulk_create([
            UserFollows(user=self.users[0], followed_user=self.users[1]),
        ])

        self.login(self.users[0])

        #cache does not exist, API ensures it exists

        request = self.client.get(reverse('user_follows_api'))

        self.assertEqual(request.status_code, 200)
        print_with_function_name(request.content)

        #check

        response_data = get_response_data(request)
        when_last_action_s = cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None)

        self.assertEqual(len(response_data['data']), 1)
        self.assertGreater(response_data['when_last_action_s'], 0)
        self.assertIsNotNone(when_last_action_s)

        #follow yourself
        #expect cache to stay the same

        #must delay, else test runs too quickly and we get same when_last_action_s
        time.sleep(2)

        request = self.client.post(
            reverse('user_follows_api'),
            data={
                'username': self.users[0].username,
                'to_follow': True
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 400)

        #check

        response_data = get_response_data(request)

        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertEqual(when_last_action_s, cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))

        #follow someone
        #expect cache to be updated

        time.sleep(2)

        request = self.client.post(
            reverse('user_follows_api'),
            data={
                'username': self.users[1].username,
                'to_follow': True
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertLess(when_last_action_s, cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))

        #unfollow someone
        #expect cache to be updated

        when_last_action_s = cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None)

        time.sleep(2)

        request = self.client.post(
            reverse('user_follows_api'),
            data={
                'username': self.users[1].username,
                'to_follow': False
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertLess(when_last_action_s, cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))

        #do GET

        when_last_action_s = cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None)

        request = self.client.get(reverse('user_follows_api'), data={'when_last_action_s': when_last_action_s})

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        response_data = get_response_data(request)

        self.assertTrue(response_data['is_up_to_date'])
        self.assertIsNone(response_data.get('when_last_action_s', None))
        self.assertIsNotNone(cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))
        self.assertEqual(when_last_action_s, cache.get(UserFollowsAPI().determine_when_last_action_s_cache_key(user_id=self.users[0].id), None))


    def test_browse_events__missing_args(self):

        full_valid_args = {
            'latest_or_best': 'latest',
            'timeframe': 'all',
            'audio_clip_role_name': 'responder',
            'next_or_back': 'back',
            'username': 'huhu',
            'likes_or_dislikes': 'dislikes',
            'audio_clip_tone_id': 1,
        }

        #all are valid kwargs but each is missing 1 important kwarg
        all_kwargs = [
            {
                'timeframe': 'all',
                'audio_clip_role_name': 'originator',
                'next_or_back': 'back',
            },
            {
                'latest_or_best': 'latest',
                'audio_clip_role_name': 'originator',
                'next_or_back': 'back',
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'next_or_back': 'back',
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'originator',
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'responder',
                'likes_or_dislikes': 'dislikes',
            },
        ]

        for kwargs in all_kwargs:

            try:

                request = self.client.get(
                    reverse(
                        'browse_events_api',
                        kwargs=kwargs
                    )
                )

            except exceptions.NoReverseMatch:

                pass

            except Exception as e:

                raise e


    def test_browse_events__faulty_args(self):

        full_valid_args = {
            'latest_or_best': 'latest',
            'timeframe': 'all',
            'audio_clip_role_name': 'responder',
            'next_or_back': 'back',
            'username': self.users[0].username,
            'likes_or_dislikes': 'dislikes',
            'audio_clip_tone_id': 1,
        }

        #all are valid kwargs but each is missing 1 important kwarg
        all_kwargs = []

        new_kwargs = full_valid_args.copy()
        new_kwargs.update({'latest_or_best': 'huh'})
        all_kwargs.append(new_kwargs)

        new_kwargs = full_valid_args.copy()
        new_kwargs.update({'timeframe': 'huh'})
        all_kwargs.append(new_kwargs)

        new_kwargs = full_valid_args.copy()
        new_kwargs.update({'audio_clip_role_name': 'abcde'})
        all_kwargs.append(new_kwargs)

        new_kwargs = full_valid_args.copy()
        new_kwargs.update({'likes_or_dislikes': 'huh'})
        all_kwargs.append(new_kwargs)

        for kwargs in all_kwargs:

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=kwargs
                )
            )

            self.assertEqual(request.status_code, 400)

        #cannot pass None
        new_kwargs = full_valid_args.copy()
        new_kwargs.update({'audio_clip_tone_id': None})

        try:

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=kwargs
                )
            )

        except exceptions.NoReverseMatch:

            pass

        except Exception as e:

            raise e


    def test_browse_events__not_found_in_db_args(self):

        all_kwargs = []

        #username

        all_kwargs.append({
            'latest_or_best': 'latest',
            'timeframe': 'all',
            'audio_clip_role_name': 'responder',
            'next_or_back': 'back',
            'username': self.users[0].username + '999',
            'likes_or_dislikes': 'dislikes',
            'audio_clip_tone_id': 1,
        })

        #audio_clip_tone

        guaranteed_non_existent_audio_clip_tone_id = AudioClipTones.objects.all().order_by('-id').values_list('id')[:1]
        guaranteed_non_existent_audio_clip_tone_id = guaranteed_non_existent_audio_clip_tone_id[0][0]
        guaranteed_non_existent_audio_clip_tone_id += 1

        all_kwargs.append({
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'responder',
                'next_or_back': 'back',
                'audio_clip_tone_id': guaranteed_non_existent_audio_clip_tone_id,
        })

        #check

        for kwargs in all_kwargs:

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=kwargs
                )
            )

            print_with_function_name(request.content)
            self.assertEqual(request.status_code, 404)


    def test_browse_events__browse_likes_dislikes__only_own_rows_allowed(self):

        self.login(self.users[0])

        #not own rows

        kwargs = {
            'latest_or_best': 'latest',
            'timeframe': 'all',
            'audio_clip_role_name': 'responder',
            'next_or_back': 'back',
            'likes_or_dislikes': 'likes',
            'username': self.users[1].username,
        }

        #check

        request = self.client.get(
            reverse(
                'browse_events_api',
                kwargs=kwargs
            )
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 403)

        #is own rows

        kwargs = {
            'latest_or_best': 'latest',
            'timeframe': 'all',
            'audio_clip_role_name': 'responder',
            'next_or_back': 'back',
            'likes_or_dislikes': 'likes',
            'username': self.users[0].username,
        }

        #check

        request = self.client.get(
            reverse(
                'browse_events_api',
                kwargs=kwargs
            )
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)


    def test_browse_events__ok(self):
        #tests are in voicewake.tests.test_metrics.Core_TestCase
        pass


    def test_audio_clip_bans__get__only_while_banned(self):

        #not banned

        self.login(self.users[0])

        request = self.client.get(
            reverse(
                'audio_clip_bans_api',
                kwargs={}
            )
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 400)

        #banned

        self.users[0].banned_until = get_datetime_now() + timedelta(seconds=10)
        self.users[0].ban_count = 1
        self.users[0].save()

        self.login(self.users[0])

        request = self.client.get(
            reverse(
                'audio_clip_bans_api',
                kwargs={}
            )
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)


    def test_audio_clip_bans__get__ok(self):

        #prepare data

        #banned as originator

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="deleted",
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
            is_banned=True
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #banned as responder

        sample_event_1 = EventsFactory(
            event_created_by=self.users[1],
            event_generic_status_generic_status_name="incomplete",
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
            audio_clip_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        sample_audio_clip_2 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_1,
            audio_clip_generic_status_generic_status_name='deleted',
            is_banned=True,
        )

        sample_audio_clip_metric_2 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_2,
        )

        #fine as originator

        sample_event_2 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name="completed",
        )

        sample_audio_clip_3 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_2,
            audio_clip_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_metric_3 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_3,
        )

        #fine as responder

        sample_event_3 = EventsFactory(
            event_created_by=self.users[1],
            event_generic_status_generic_status_name="completed",
        )

        sample_audio_clip_4 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_3,
            audio_clip_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_metric_4 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_4,
        )

        sample_audio_clip_5 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_3,
            audio_clip_generic_status_generic_status_name='ok',
        )

        sample_audio_clip_metric_5 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_5,
        )

        #start

        self.users[0].banned_until = get_datetime_now() + timedelta(seconds=10)
        self.users[0].ban_count = 1
        self.users[0].save()

        self.login(self.users[0])

        request = self.client.get(
            reverse(
                'audio_clip_bans_api',
            )
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        response_data = get_response_data(request)

        banned_audio_clip_ids = [sample_audio_clip_0.id, sample_audio_clip_2.id]

        self.assertEqual(len(response_data['data']), 2)
        self.assertTrue(response_data['data'][0]['id'] in banned_audio_clip_ids)
        self.assertTrue(response_data['data'][1]['id'] in banned_audio_clip_ids)
        self.assertNotEqual(response_data['data'][0]['id'], response_data['data'][1]['id'])


    def test_audio_clip_bans__post__superuser_ok(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            like_count=1,
            dislike_count=1,
            like_ratio=0.5,
        )
        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
            audio_clip=sample_audio_clip_0,
            user=self.users[1],
            is_liked=True
        )
        sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
            audio_clip=sample_audio_clip_0,
            user=self.users[2],
            is_liked=False
        )
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            audio_clip=sample_audio_clip_0,
            last_evaluated=None,
        )

        sample_event_1 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_1,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
            like_count=1,
            dislike_count=1,
            like_ratio=0.5,
        )
        sample_audio_clip_like_dislike_2 = AudioClipLikesDislikes.objects.create(
            audio_clip=sample_audio_clip_1,
            user=self.users[1],
            is_liked=True
        )
        sample_audio_clip_like_dislike_3 = AudioClipLikesDislikes.objects.create(
            audio_clip=sample_audio_clip_1,
            user=self.users[2],
            is_liked=False
        )

        #try when not superuser

        self.assertFalse(self.users[1].is_superuser)

        self.login(self.users[1])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        self.assertEqual(request.status_code, 403)

        #try when superuser

        self.users[1].is_superuser = True
        self.users[1].save()

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check
        #for duration calculation, do +-10s for fault tolerance during testing

        self.users[0].refresh_from_db()
        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        banned_until_day_difference = settings.ADMIN_AUDIO_CLIP_BASE_BAN_DAYS ** self.users[0].ban_count

        self.assertEqual(self.users[0].ban_count, 1)
        self.assertLess(self.users[0].banned_until, (get_datetime_now() + timedelta(days=banned_until_day_difference, seconds=10)))
        self.assertGreater(self.users[0].banned_until, (get_datetime_now() - timedelta(days=banned_until_day_difference, seconds=10)))
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertFalse(AudioClipReports.objects.filter(audio_clip=sample_audio_clip_0).exists())
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)

        #determine ban_count needed to exceed settings.ADMIN_AUDIO_CLIP_MAX_BAN_DAYS

        minimum_ban_count = 0

        while (settings.ADMIN_AUDIO_CLIP_BASE_BAN_DAYS ** minimum_ban_count) < settings.ADMIN_AUDIO_CLIP_MAX_BAN_DAYS:

            minimum_ban_count += 1

        self.users[0].ban_count = minimum_ban_count
        self.users[0].save()

        #superuser shall ban again

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        #check

        self.users[0].refresh_from_db()
        sample_event_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        banned_until_day_difference = settings.ADMIN_AUDIO_CLIP_MAX_BAN_DAYS

        self.assertEqual(self.users[0].ban_count, minimum_ban_count+1)
        self.assertLess(self.users[0].banned_until, (get_datetime_now() + timedelta(days=banned_until_day_difference, seconds=10)))
        self.assertGreater(self.users[0].banned_until, (get_datetime_now() - timedelta(days=banned_until_day_difference, seconds=10)))
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertFalse(AudioClipReports.objects.filter(audio_clip=sample_audio_clip_1).exists())
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 0)

        #try to ban audio_clip that's already banned

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)


    def test_audio_clip_bans__post__no_permission(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            audio_clip_metric_like_count=1,
            audio_clip_metric_dislike_count=1,
            audio_clip_metric_like_ratio=0.5,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
            audio_clip_metric_like_count=1,
            audio_clip_metric_dislike_count=1,
            audio_clip_metric_like_ratio=0.5,
        )
        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
            user=self.users[1],
            audio_clip=sample_audio_clip_0,
            is_liked=True
        )
        sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
            user=self.users[2],
            audio_clip=sample_audio_clip_0,
            is_liked=False
        )
        sample_audio_clip_like_dislike_2 = AudioClipLikesDislikes.objects.create(
            user=self.users[1],
            audio_clip=sample_audio_clip_1,
            is_liked=True
        )
        sample_audio_clip_like_dislike_3 = AudioClipLikesDislikes.objects.create(
            user=self.users[2],
            audio_clip=sample_audio_clip_1,
            is_liked=False
        )

        #originator

        #as themselves

        self.login(self.users[0])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        self.assertEqual(request.status_code, 403)

        #as opposite role

        self.login(self.users[1])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        self.assertEqual(request.status_code, 403)

        #as random user

        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        self.assertEqual(request.status_code, 403)

        #responder

        #as themselves

        self.login(self.users[0])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        self.assertEqual(request.status_code, 403)

        #as opposite role

        self.login(self.users[1])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        self.assertEqual(request.status_code, 403)

        #as random user

        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        self.assertEqual(request.status_code, 403)

        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()
        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()

        self.assertEqual(self.users[0].ban_count, 0)
        self.assertIsNone(self.users[0].banned_until)
        self.assertEqual(self.users[1].ban_count, 0)
        self.assertIsNone(self.users[1].banned_until)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'completed')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'ok')
        self.assertFalse(sample_audio_clip_0.is_banned)
        self.assertFalse(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 1)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 1)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0.5)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0.5)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 2)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 2)


    def test_audio_clip_bans__post__incomplete__ban_originator(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        self.login(self.users[3])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            like_count=1,
            dislike_count=1,
            like_ratio=0.5,
        )
        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
            audio_clip=sample_audio_clip_0,
            user=self.users[1],
            is_liked=True
        )
        sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
            audio_clip=sample_audio_clip_0,
            user=self.users[2],
            is_liked=False
        )

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        self.users[0].refresh_from_db()
        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()

        self.assertEqual(self.users[0].ban_count, 1)
        self.assertIsNotNone(self.users[0].banned_until)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)


    def test_audio_clip_bans__post__completed__ban_originator(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        self.login(self.users[3])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            like_count=1,
            dislike_count=1,
            like_ratio=0.5,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
            like_count=1,
            dislike_count=1,
            like_ratio=0.5,
        )
        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
            audio_clip=sample_audio_clip_0,
            user=self.users[1],
            is_liked=True
        )
        sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
            audio_clip=sample_audio_clip_0,
            user=self.users[2],
            is_liked=False
        )
        sample_audio_clip_like_dislike_2 = AudioClipLikesDislikes.objects.create(
            audio_clip=sample_audio_clip_1,
            user=self.users[1],
            is_liked=True
        )
        sample_audio_clip_like_dislike_3 = AudioClipLikesDislikes.objects.create(
            audio_clip=sample_audio_clip_1,
            user=self.users[2],
            is_liked=False
        )

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        self.users[0].refresh_from_db()
        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()

        self.assertEqual(self.users[0].ban_count, 1)
        self.assertIsNotNone(self.users[0].banned_until)
        self.assertEqual(self.users[1].ban_count, 0)
        self.assertIsNone(self.users[1].banned_until)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'ok')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertFalse(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0.5)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 2)


    def test_audio_clip_bans__post__completed__ban_responder(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        self.login(self.users[3])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            audio_clip_metric_like_count=1,
            audio_clip_metric_dislike_count=1,
            audio_clip_metric_like_ratio=0.5,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
            audio_clip_metric_like_count=1,
            audio_clip_metric_dislike_count=1,
            audio_clip_metric_like_ratio=0.5,
        )
        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
            user=self.users[1],
            audio_clip=sample_audio_clip_0,
            is_liked=True
        )
        sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
            user=self.users[2],
            audio_clip=sample_audio_clip_0,
            is_liked=False
        )
        sample_audio_clip_like_dislike_2 = AudioClipLikesDislikes.objects.create(
            user=self.users[1],
            audio_clip=sample_audio_clip_1,
            is_liked=True
        )
        sample_audio_clip_like_dislike_3 = AudioClipLikesDislikes.objects.create(
            user=self.users[2],
            audio_clip=sample_audio_clip_1,
            is_liked=False
        )

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()
        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()

        self.assertEqual(self.users[0].ban_count, 0)
        self.assertIsNone(self.users[0].banned_until)
        self.assertEqual(self.users[1].ban_count, 1)
        self.assertIsNotNone(self.users[1].banned_until)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertFalse(sample_audio_clip_0.is_banned)
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 1)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 1)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0.5)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 2)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 0)


    def test_audio_clip_bans__post__originator_banned__ban_responder(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        self.login(self.users[3])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='deleted',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
            is_banned=True,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
            audio_clip_metric_like_count=1,
            audio_clip_metric_dislike_count=1,
            audio_clip_metric_like_ratio=0.5,
        )
        sample_audio_clip_like_dislike_2 = AudioClipLikesDislikes.objects.create(
            user=self.users[1],
            audio_clip=sample_audio_clip_1,
            is_liked=True
        )
        sample_audio_clip_like_dislike_3 = AudioClipLikesDislikes.objects.create(
            user=self.users[2],
            audio_clip=sample_audio_clip_1,
            is_liked=False
        )

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)

        self.users[0].refresh_from_db()
        self.users[1].refresh_from_db()
        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()

        self.assertEqual(self.users[0].ban_count, 0)
        self.assertIsNone(self.users[0].banned_until)
        self.assertEqual(self.users[1].ban_count, 1)
        self.assertIsNotNone(self.users[1].banned_until)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 0)


    def test_audio_clip_bans__post__audio_clip__unaffected(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        self.login(self.users[3])

        #not yet available

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 400)

        #already banned

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='deleted',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
            is_banned=True
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 200)


    def test_audio_clip_bans__post__ban_banned_audio_clip(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[1],
            event_generic_status_generic_status_name='completed',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
            is_banned=False,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
            is_banned=False,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #prepare

        self.users[0].is_superuser = True
        self.users[0].save()
        self.login(self.users[0])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        self.assertEqual(request.status_code, 200)

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        self.assertEqual(request.status_code, 200)

        #start

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        self.assertEqual(request.status_code, 200)

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        self.assertEqual(request.status_code, 200)

        print_with_function_name(request.content)

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        self.users[1].refresh_from_db()

        self.assertEqual(self.users[1].ban_count, 1)
        self.assertIsNotNone(self.users[1].banned_until)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)

        sample_event_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        self.users[2].refresh_from_db()

        self.assertEqual(self.users[2].ban_count, 1)
        self.assertIsNotNone(self.users[2].banned_until)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 0)


    def test_audio_clip_bans__post__ban_deleted_audio_clip(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[1],
            event_generic_status_generic_status_name='deleted',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
            is_banned=False
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
            is_banned=False
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #start

        self.users[0].is_superuser = True
        self.users[0].save()
        self.login(self.users[0])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        print_with_function_name(request.content)

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        self.users[1].refresh_from_db()

        self.assertEqual(request.status_code, 200)
        self.assertEqual(self.users[1].ban_count, 1)
        self.assertIsNotNone(self.users[1].banned_until)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)

        #start

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        print_with_function_name(request.content)

        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        self.users[2].refresh_from_db()

        self.assertEqual(request.status_code, 200)
        self.assertEqual(self.users[2].ban_count, 1)
        self.assertIsNotNone(self.users[2].banned_until)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 0)


    def test_audio_clip_bans__post__cannot_ban_yourself(self):

        self.users[0].is_superuser = True
        self.users[0].save()

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='incomplete',
            is_banned=False
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            audio_clip_metric_like_count=1,
            audio_clip_metric_dislike_count=1,
            audio_clip_metric_like_ratio=0.5,
        )
        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
            user=self.users[0],
            audio_clip=sample_audio_clip_0,
            is_liked=True
        )
        sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
            user=self.users[1],
            audio_clip=sample_audio_clip_0,
            is_liked=False
        )

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        print_with_function_name(request.content)

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        self.users[0].refresh_from_db()

        self.assertEqual(request.status_code, 400)
        self.assertEqual(self.users[0].ban_count, 0)


    def test_audio_clip_bans__idempotence(self):


        sample_event_0 = EventsFactory(
            event_created_by=self.users[1],
            event_generic_status_generic_status_name='deleted',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
            is_banned=False,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[2],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
            is_banned=False,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #start

        self.users[0].is_superuser = True
        self.users[0].save()
        self.login(self.users[0])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        self.assertEqual(request.status_code, 200)

        #idempotence
        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            }
        )

        self.assertEqual(request.status_code, 200)

        print_with_function_name(request.content)

        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()
        self.users[1].refresh_from_db()

        self.assertEqual(self.users[1].ban_count, 1)
        self.assertIsNotNone(self.users[1].banned_until)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)

        #start

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        self.assertEqual(request.status_code, 200)

        #idempotence
        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            }
        )

        self.assertEqual(request.status_code, 200)

        print_with_function_name(request.content)

        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()
        self.users[2].refresh_from_db()

        self.assertEqual(self.users[2].ban_count, 1)
        self.assertIsNotNone(self.users[2].banned_until)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 0)


    def test_audio_clip_bans__post__no_rows(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        self.login(self.users[3])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': 999999999,
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 404)


    def test_audio_clip_bans__post__missing_args(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        self.login(self.users[3])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 400)


    def test_audio_clip_bans__post__faulty_args(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        self.login(self.users[3])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': '@',
            }
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 400)


    def test_audio_clip_delete__superuser_or_themselves_ok(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            like_count=1,
            dislike_count=1,
            like_ratio=0.5,
        )
        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
            user=self.users[0],
            audio_clip=sample_audio_clip_0,
            is_liked=True
        )
        sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
            user=self.users[1],
            audio_clip=sample_audio_clip_0,
            is_liked=False
        )

        #try when not superuser

        self.assertFalse(self.users[1].is_superuser)

        self.login(self.users[1])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 403)

        #try when superuser

        self.users[1].is_superuser = True
        self.users[1].save()

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()

        self.assertEqual(request.status_code, 204)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)

        #try as themselves

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            like_count=1,
            dislike_count=1,
            like_ratio=0.5,
        )
        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
            user=self.users[0],
            audio_clip=sample_audio_clip_0,
            is_liked=True
        )
        sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
            user=self.users[1],
            audio_clip=sample_audio_clip_0,
            is_liked=False
        )

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()

        self.assertEqual(request.status_code, 204)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)


    def test_audio_clip_delete__no_permission(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            like_count=1,
            dislike_count=1,
            like_ratio=0.5,
        )
        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
            user=self.users[0],
            audio_clip=sample_audio_clip_0,
            is_liked=True
        )
        sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
            user=self.users[1],
            audio_clip=sample_audio_clip_0,
            is_liked=False
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
            like_count=1,
            dislike_count=1,
            like_ratio=0.5,
        )
        sample_audio_clip_like_dislike_2 = AudioClipLikesDislikes.objects.create(
            user=self.users[0],
            audio_clip=sample_audio_clip_1,
            is_liked=True
        )
        sample_audio_clip_like_dislike_3 = AudioClipLikesDislikes.objects.create(
            user=self.users[1],
            audio_clip=sample_audio_clip_1,
            is_liked=False
        )

        #originator

        #try as random user

        self.login(self.users[2])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 403)

        #try as opposite role

        self.login(self.users[1])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 403)

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'completed')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 2)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0.5)

        #responder

        #try as random user

        self.login(self.users[2])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_1.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 403)

        #try as opposite role

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_1.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 403)

        sample_event_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'completed')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'ok')
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 2)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 1)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 1)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0.5)


    def test_audio_clip_delete__delete_reported_audio_clip(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
            like_count=1,
            dislike_count=1,
            like_ratio=0.5,
        )
        sample_audio_clip_report_0 = AudioClipReports.objects.create(
            audio_clip=sample_audio_clip_0,
            last_evaluated=None,
        )
        sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
            user=self.users[0],
            audio_clip=sample_audio_clip_0,
            is_liked=True
        )
        sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
            user=self.users[1],
            audio_clip=sample_audio_clip_0,
            is_liked=False
        )

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()

        self.assertEqual(request.status_code, 204)
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(AudioClipReports.objects.filter(pk=sample_audio_clip_report_0.id).exists())
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 1)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0.5)


    def test_audio_clip_delete__incomplete__delete_originator(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        all_users = [
            self.users[0],
            self.users[3]
        ]

        for user in all_users:

            self.login(user)

            sample_event_0 = EventsFactory(
                event_created_by=user,
                event_generic_status_generic_status_name='incomplete',
            )
            sample_audio_clip_0 = AudioClipsFactory(
                audio_clip_user=user,
                audio_clip_audio_clip_role_audio_clip_role_name='originator',
                audio_clip_event=sample_event_0,
                audio_clip_generic_status_generic_status_name='ok',
            )
            sample_audio_clip_metric_0 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_0,
                like_count=1,
                dislike_count=1,
                like_ratio=0.5,
            )
            sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
                user=user,
                audio_clip=sample_audio_clip_0,
                is_liked=True
            )
            sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
                user=self.users[2],
                audio_clip=sample_audio_clip_0,
                is_liked=False
            )

            request = self.client.delete(
                reverse(
                    'audio_clip_deletions_api',
                    kwargs={
                    'audio_clip_id': sample_audio_clip_0.id,
                    },
                ),
            )

            print_with_function_name(request.content)
            self.assertEqual(request.status_code, 204)

            self.users[0].refresh_from_db()
            sample_event_0.refresh_from_db()
            sample_audio_clip_0.refresh_from_db()
            sample_audio_clip_metric_0.refresh_from_db()

            self.assertEqual(self.users[0].ban_count, 0)
            self.assertIsNone(self.users[0].banned_until)
            self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
            self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
            self.assertFalse(sample_audio_clip_0.is_banned)
            self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
            self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
            self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
            self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)


    def test_audio_clip_delete__completed__delete_originator(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        all_users = [
            self.users[0],
            self.users[3]
        ]

        for user in all_users:

            self.login(user)

            sample_event_0 = EventsFactory(
                event_created_by=user,
                event_generic_status_generic_status_name='completed',
            )
            sample_audio_clip_0 = AudioClipsFactory(
                audio_clip_user=user,
                audio_clip_audio_clip_role_audio_clip_role_name='originator',
                audio_clip_event=sample_event_0,
                audio_clip_generic_status_generic_status_name='ok',
            )
            sample_audio_clip_metric_0 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_0,
                like_count=1,
                dislike_count=1,
                like_ratio=0.5,
            )
            sample_audio_clip_1 = AudioClipsFactory(
                audio_clip_user=self.users[1],
                audio_clip_audio_clip_role_audio_clip_role_name='responder',
                audio_clip_event=sample_event_0,
                audio_clip_generic_status_generic_status_name='ok',
            )
            sample_audio_clip_metric_1 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_1,
                like_count=1,
                dislike_count=1,
                like_ratio=0.5,
            )
            sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
                user=user,
                audio_clip=sample_audio_clip_0,
                is_liked=True
            )
            sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
                user=self.users[2],
                audio_clip=sample_audio_clip_0,
                is_liked=False
            )
            sample_audio_clip_like_dislike_2 = AudioClipLikesDislikes.objects.create(
                user=user,
                audio_clip=sample_audio_clip_1,
                is_liked=True
            )
            sample_audio_clip_like_dislike_3 = AudioClipLikesDislikes.objects.create(
                user=self.users[2],
                audio_clip=sample_audio_clip_1,
                is_liked=False
            )

            request = self.client.delete(
                reverse(
                    'audio_clip_deletions_api',
                    kwargs={
                    'audio_clip_id': sample_audio_clip_0.id,
                    },
                ),
            )

            print_with_function_name(request.content)
            self.assertEqual(request.status_code, 204)

            self.users[0].refresh_from_db()
            sample_event_0.refresh_from_db()
            sample_audio_clip_0.refresh_from_db()
            sample_audio_clip_metric_0.refresh_from_db()

            self.assertEqual(self.users[0].ban_count, 0)
            self.assertIsNone(self.users[0].banned_until)
            self.assertEqual(self.users[1].ban_count, 0)
            self.assertIsNone(self.users[1].banned_until)
            self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
            self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
            self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'ok')
            self.assertFalse(sample_audio_clip_0.is_banned)
            self.assertFalse(sample_audio_clip_1.is_banned)
            self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
            self.assertEqual(sample_audio_clip_metric_1.like_count, 1)
            self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
            self.assertEqual(sample_audio_clip_metric_1.dislike_count, 1)
            self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
            self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0.5)
            self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)
            self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 2)


    def test_audio_clip_delete__completed__delete_responder(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        all_users = [
            self.users[0],
            self.users[3]
        ]

        for user in all_users:

            self.login(user)

            sample_event_0 = EventsFactory(
                event_created_by=self.users[0],
                event_generic_status_generic_status_name='completed',
            )
            sample_audio_clip_0 = AudioClipsFactory(
                audio_clip_user=self.users[0],
                audio_clip_audio_clip_role_audio_clip_role_name='originator',
                audio_clip_event=sample_event_0,
                audio_clip_generic_status_generic_status_name='ok',
            )
            sample_audio_clip_metric_0 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_0,
                audio_clip_metric_like_count=1,
                audio_clip_metric_dislike_count=1,
                audio_clip_metric_like_ratio=0.5,
            )
            sample_audio_clip_1 = AudioClipsFactory(
                audio_clip_user=user,
                audio_clip_audio_clip_role_audio_clip_role_name='responder',
                audio_clip_event=sample_event_0,
                audio_clip_generic_status_generic_status_name='ok',
            )
            sample_audio_clip_metric_1 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_1,
                audio_clip_metric_like_count=1,
                audio_clip_metric_dislike_count=1,
                audio_clip_metric_like_ratio=0.5,
            )
            sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
                user=user,
                audio_clip=sample_audio_clip_0,
                is_liked=True
            )
            sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
                user=self.users[2],
                audio_clip=sample_audio_clip_0,
                is_liked=False
            )
            sample_audio_clip_like_dislike_2 = AudioClipLikesDislikes.objects.create(
                user=user,
                audio_clip=sample_audio_clip_1,
                is_liked=True
            )
            sample_audio_clip_like_dislike_3 = AudioClipLikesDislikes.objects.create(
                user=self.users[2],
                audio_clip=sample_audio_clip_1,
                is_liked=False
            )

            request = self.client.delete(
                reverse(
                    'audio_clip_deletions_api',
                    kwargs={
                    'audio_clip_id': sample_audio_clip_1.id,
                    },
                ),
            )

            print_with_function_name(request.content)
            self.assertEqual(request.status_code, 204)

            self.users[0].refresh_from_db()
            sample_event_0.refresh_from_db()
            sample_audio_clip_0.refresh_from_db()
            sample_audio_clip_metric_0.refresh_from_db()
            sample_audio_clip_1.refresh_from_db()
            sample_audio_clip_metric_1.refresh_from_db()

            self.assertEqual(self.users[0].ban_count, 0)
            self.assertIsNone(self.users[0].banned_until)
            self.assertEqual(self.users[1].ban_count, 0)
            self.assertIsNone(self.users[1].banned_until)
            self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
            self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
            self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
            self.assertFalse(sample_audio_clip_0.is_banned)
            self.assertFalse(sample_audio_clip_1.is_banned)
            self.assertEqual(sample_audio_clip_metric_0.like_count, 1)
            self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
            self.assertEqual(sample_audio_clip_metric_0.dislike_count, 1)
            self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
            self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0.5)
            self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
            self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 2)
            self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 0)


    def test_audio_clip_delete__originator_deleted__delete_responder(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        all_users = [
            self.users[0],
            self.users[3]
        ]

        for user in all_users:

            self.login(user)

            sample_event_0 = EventsFactory(
                event_created_by=self.users[0],
                event_generic_status_generic_status_name='deleted',
            )
            sample_audio_clip_0 = AudioClipsFactory(
                audio_clip_user=self.users[0],
                audio_clip_audio_clip_role_audio_clip_role_name='originator',
                audio_clip_event=sample_event_0,
                audio_clip_generic_status_generic_status_name='deleted',
            )
            sample_audio_clip_metric_0 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_0,
            )
            sample_audio_clip_1 = AudioClipsFactory(
                audio_clip_user=user,
                audio_clip_audio_clip_role_audio_clip_role_name='responder',
                audio_clip_event=sample_event_0,
                audio_clip_generic_status_generic_status_name='ok',
            )
            sample_audio_clip_metric_1 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_1,
                like_count=1,
                dislike_count=1,
                like_ratio=0.5,
            )
            sample_audio_clip_like_dislike_2 = AudioClipLikesDislikes.objects.create(
                user=self.users[1],
                audio_clip=sample_audio_clip_1,
                is_liked=True
            )
            sample_audio_clip_like_dislike_3 = AudioClipLikesDislikes.objects.create(
                user=self.users[2],
                audio_clip=sample_audio_clip_1,
                is_liked=False
            )

            request = self.client.delete(
                reverse(
                    'audio_clip_deletions_api',
                    kwargs={
                    'audio_clip_id': sample_audio_clip_1.id,
                    },
                ),
            )

            print_with_function_name(request.content)
            self.assertEqual(request.status_code, 204)

            self.users[0].refresh_from_db()
            sample_event_0.refresh_from_db()
            sample_audio_clip_0.refresh_from_db()
            sample_audio_clip_metric_0.refresh_from_db()
            sample_audio_clip_1.refresh_from_db()
            sample_audio_clip_metric_1.refresh_from_db()

            self.assertEqual(self.users[0].ban_count, 0)
            self.assertIsNone(self.users[0].banned_until)
            self.assertEqual(self.users[1].ban_count, 0)
            self.assertIsNone(self.users[1].banned_until)
            self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
            self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
            self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
            self.assertFalse(sample_audio_clip_0.is_banned)
            self.assertFalse(sample_audio_clip_1.is_banned)
            self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
            self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
            self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
            self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
            self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
            self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
            self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)
            self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 0)


    def test_audio_clip_delete__processing__delete_unaffected(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        self.login(self.users[3])

        #not yet available

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 400)

        #already banned

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='deleted',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
            is_banned=True,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 204)

        #already deleted

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='deleted',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='deleted',
            is_banned=False,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 204)


    def test_audio_clip_delete__delete_deleted_audio_clip(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #delete both

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 204)

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_1.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 204)

        #delete as originator

        #cannot while user is banned
        self.users[0].banned_until = get_datetime_now() + timedelta(days=1)
        self.users[0].save()

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 403)

        #unban
        self.users[0].banned_until = None
        self.users[0].save()

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        #ok
        self.assertEqual(request.status_code, 204)

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertFalse(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)

        #delete as responder

        #cannot while user is banned
        self.users[1].banned_until = get_datetime_now() + timedelta(days=1)
        self.users[1].save()

        self.login(self.users[1])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_1.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 403)

        #unban
        self.users[1].banned_until = None
        self.users[1].save()

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_1.id,
                },
            ),
        )

        #ok
        self.assertEqual(request.status_code, 204)

        sample_event_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertFalse(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 0)


    def test_audio_clip_delete__delete_banned_audio_clip(self):

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='completed',
        )
        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )
        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #ban both

        self.users[2].is_superuser = True
        self.users[2].save()
        self.login(self.users[2])

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_0.id,
            },
        )

        self.assertEqual(request.status_code, 200)

        request = self.client.post(
            reverse('audio_clip_bans_api'),
            data={
                'audio_clip_id': sample_audio_clip_1.id,
            },
        )

        self.assertEqual(request.status_code, 200)

        #delete as originator

        self.login(self.users[0])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 403)

        #unban
        self.users[0].banned_until = None
        self.users[0].save()

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_0.id,
                },
            ),
        )

        #ok
        self.assertEqual(request.status_code, 204)

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
        sample_audio_clip_metric_0.refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_0.is_banned)
        self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)

        #delete as responder

        self.login(self.users[1])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_1.id,
                },
            ),
        )

        self.assertEqual(request.status_code, 403)

        #unban
        self.users[1].banned_until = None
        self.users[1].save()

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': sample_audio_clip_1.id,
                },
            ),
        )

        #ok
        self.assertEqual(request.status_code, 204)

        sample_event_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
        sample_audio_clip_metric_1.refresh_from_db()

        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'deleted')
        self.assertTrue(sample_audio_clip_1.is_banned)
        self.assertEqual(sample_audio_clip_metric_1.like_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.dislike_count, 0)
        self.assertEqual(sample_audio_clip_metric_1.like_ratio, 0)
        self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_1).count(), 0)


    def test_audio_clip_delete__idempotence(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        all_users = [
            self.users[0],
            self.users[0],
            self.users[3],
            self.users[3],
        ]

        for user in all_users:

            self.login(user)

            sample_event_0 = EventsFactory(
                event_created_by=user,
                event_generic_status_generic_status_name='incomplete',
            )
            sample_audio_clip_0 = AudioClipsFactory(
                audio_clip_user=user,
                audio_clip_audio_clip_role_audio_clip_role_name='originator',
                audio_clip_event=sample_event_0,
                audio_clip_generic_status_generic_status_name='ok',
            )
            sample_audio_clip_metric_0 = AudioClipMetricsFactory(
                audio_clip_metric_audio_clip=sample_audio_clip_0,
                like_count=1,
                dislike_count=1,
                like_ratio=0.5,
            )
            sample_audio_clip_like_dislike_0 = AudioClipLikesDislikes.objects.create(
                user=user,
                audio_clip=sample_audio_clip_0,
                is_liked=True
            )
            sample_audio_clip_like_dislike_1 = AudioClipLikesDislikes.objects.create(
                user=self.users[2],
                audio_clip=sample_audio_clip_0,
                is_liked=False
            )

            request = self.client.delete(
                reverse(
                    'audio_clip_deletions_api',
                    kwargs={
                    'audio_clip_id': sample_audio_clip_0.id,
                    },
                ),
            )

            print_with_function_name(request.content)
            self.assertEqual(request.status_code, 204)

            self.users[0].refresh_from_db()
            sample_event_0.refresh_from_db()
            sample_audio_clip_0.refresh_from_db()
            sample_audio_clip_metric_0.refresh_from_db()

            self.assertEqual(self.users[0].ban_count, 0)
            self.assertIsNone(self.users[0].banned_until)
            self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
            self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'deleted')
            self.assertFalse(sample_audio_clip_0.is_banned)
            self.assertEqual(sample_audio_clip_metric_0.like_count, 0)
            self.assertEqual(sample_audio_clip_metric_0.dislike_count, 0)
            self.assertEqual(sample_audio_clip_metric_0.like_ratio, 0)
            self.assertEqual(AudioClipLikesDislikes.objects.filter(audio_clip=sample_audio_clip_0).count(), 0)


    def test_audio_clip_deletions__no_rows(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        self.login(self.users[3])

        request = self.client.delete(
            reverse(
                'audio_clip_deletions_api',
                kwargs={
                'audio_clip_id': 99999999,
                },
            ),
        )

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 404)


    def test_audio_clip_deletions__post__missing_args(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        self.login(self.users[3])

        request = self.client.delete('api/audio-clips/delete')

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 404)


    def test_audio_clip_deletions__post__faulty_args(self):

        self.users[3].is_superuser = True
        self.users[3].save()

        self.login(self.users[3])

        request = self.client.delete('api/audio-clips/delete/@')

        print_with_function_name(request.content)
        self.assertEqual(request.status_code, 404)









#these involve AWS in one way or another
#for test cases with Redis, only way to guarantee cache isolation have unique target_user for every test case
#cannot chain first+next+last attempts in one single test case, because we're also testing how cache is guaranteed to exist at all attempts
@override_settings(
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

        #local file paths
        cls.shorter_audio_file_full_path = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/audio_ok_10s.webm'
        )
        cls.longer_audio_file_full_path = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/audio_ok_120s.webm'
        )
        cls.faulty_audio_file_full_path_0 = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/txt_as_fake_webm.webm'
        )
        cls.faulty_audio_file_full_path_1 = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/audio_not_mp3.wav'
        )

        #files
        with open(cls.shorter_audio_file_full_path, 'rb') as file_stream:
            cls.shorter_audio_clip_audio_file=SimpleUploadedFile('sample_audio_file.webm', file_stream.read(), 'audio/webm')

        #objects in s3 should exist before starting tests

        #unprocessed/processed object keys in S3
        cls.unprocessed_object_key = 'test/audio_ok_10s.webm'
        cls.processed_object_key = 'test/audio_ok_10s.mp3'

        #ensure test files exist in s3 before we run tests
        cls._prepare_s3_unprocessed_audio_file(
            unprocessed_object_key=cls.unprocessed_object_key,
            file_extension='webm',
            local_file_path=cls.shorter_audio_file_full_path
        )

        #ensure faulty file exists
        cls.faulty_audio_file_unprocessed_object_key_0 = 'test/text_as_fake_webm.webm'
        cls.faulty_audio_file_unprocessed_object_key_1 = 'test/audio_not_mp3.wav'

        cls._prepare_s3_unprocessed_audio_file(
            unprocessed_object_key=cls.faulty_audio_file_unprocessed_object_key_0,
            file_extension='webm',
            local_file_path=cls.faulty_audio_file_full_path_0
        )

    @classmethod
    def tearDownClass(cls):

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


    def create_user(self):

        random_string = get_random_string(10)

        current_user = get_user_model().objects.create_user(
            username='useR'+random_string,
            email='user'+random_string+'@gmail.com',
        )

        current_user = get_user_model().objects.get(username_lowercase="user"+random_string)

        current_user.is_active = True
        current_user.save()

        return current_user


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
            s3_audio_file_max_size_b=settings.AWS_S3_AUDIO_FILE_MAX_SIZE_B,
            url_expiry_s=settings.AWS_S3_UPLOAD_URL_EXPIRY_S,
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
            timeout_s=settings.AWS_LAMBDA_NORMALISE_TIMEOUT_S,
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


    #chances of redis crashing within the <20s processing time is rare enough to not worry about
    #no way for user to manually crash redis
    def test_edge_case__create_events__process__cache_gone_means_attempt_count_lost(self):

        #do first attempt fail > delete cache > do next attempt fail

        #since cache uses user.id, always create new user for every test case to ensure cache isolation
        target_user = self.create_user()

        self.login(target_user)

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=target_user.id,
        )

        #must not exist first
        self.assertIsNone(
            cache.get(target_cache_key, None)
        )

        sample_event_0 = EventsFactory(
            event_created_by = target_user,
            event_generic_status_generic_status_name = 'processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=target_user,
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing_pending',
            audio_clip_audio_file=self.faulty_audio_file_unprocessed_object_key_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #first and next attempts
        for loop_count in range(2):

            #proceed
    
            data = {
                'audio_clip_id': sample_audio_clip_0.id,
            }
    
            request = self.client.post(reverse('create_events_process_api'), data)
            response_data = get_response_data(request)
    
            self.assertEqual(request.status_code, 200)

            sample_event_0.refresh_from_db()
            sample_audio_clip_0.refresh_from_db()
    
            #has cache and processing object on normalise failure
            #frontend uses last version of cache to check for completion

            target_cache = cache.get(target_cache_key, None)

            self.assertEqual(sample_event_0.generic_status.generic_status_name, 'processing')
            self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'processing_failed')
            self.assertEqual(
                sample_audio_clip_0.audio_file,
                self.faulty_audio_file_unprocessed_object_key_0
            )

            self.assertIsNotNone(target_cache)
            self.assertTrue(str(sample_audio_clip_0.id) in target_cache['processings'])
            self.assertEqual(
                target_cache['processings'][str(sample_audio_clip_0.id)]['status'],
                sample_audio_clip_0.generic_status.generic_status_name
            )

            #this is the proof
            self.assertEqual(
                target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'],
                settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
            )

            #don't evaluate actual value, as it is always -1 in test, but has late -1 in prod due to the nature of task queue
            self.assertTrue('attempts_left' in response_data)

            #delete cache to prove it
            cache.set(target_cache_key, None)


    #chances of redis crashing within the <20s processing time is rare enough to not worry about
    #no way for user to manually crash redis
    def test_edge_case__create_replies__process__cache_gone_means_attempt_count_lost(self):

        #do first attempt fail > delete cache > do next attempt fail

        #since cache uses user.id, always create new user for every test case to ensure cache isolation
        target_user = self.create_user()

        self.login(target_user)

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=target_user.id,
        )

        #must not exist first
        self.assertIsNone(
            cache.get(target_cache_key, None)
        )

        sample_event_0 = EventsFactory(
            event_created_by = self.users[0],
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=target_user,
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
            audio_clip_audio_file=self.processed_object_key,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=target_user.id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=target_user,
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing_pending',
            audio_clip_audio_file=self.faulty_audio_file_unprocessed_object_key_0,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #first and next attempts
        for loop_count in range(2):

            #proceed
    
            data = {
                'audio_clip_id': sample_audio_clip_1.id,
            }
    
            request = self.client.post(reverse('create_replies_process_api'), data)
            response_data = get_response_data(request)
    
            self.assertEqual(request.status_code, 200)

            sample_event_0.refresh_from_db()
            sample_audio_clip_0.refresh_from_db()
            sample_audio_clip_1.refresh_from_db()
    
            #has cache and processing object on normalise failure
            #frontend uses last version of cache to check for completion

            target_cache = cache.get(target_cache_key, None)

            self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
            self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')
            self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'processing_failed')
            self.assertEqual(
                sample_audio_clip_1.audio_file,
                self.faulty_audio_file_unprocessed_object_key_0
            )
            self.assertTrue(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())

            self.assertIsNotNone(target_cache)
            self.assertTrue(str(sample_audio_clip_1.id) in target_cache['processings'])
            self.assertEqual(
                target_cache['processings'][str(sample_audio_clip_1.id)]['status'],
                sample_audio_clip_1.generic_status.generic_status_name
            )

            #this is the proof
            self.assertEqual(
                target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'],
                settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
            )

            #don't evaluate actual value, as it is always -1 in test, but has late -1 in prod due to the nature of task queue
            self.assertTrue('attempts_left' in response_data)

            #delete cache to prove it
            cache.set(target_cache_key, None)


    #not_consecutive means once an attempt is ok, the rows cannot be reused
    def test_create_events__process__not_consecutive__first_next_last_attempts_ok(self):

        #since cache uses user.id, always create new user for every test case to ensure cache isolation
        target_user = self.create_user()

        self.login(target_user)

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=target_user.id,
        )

        #must not exist first
        self.assertIsNone(
            cache.get(target_cache_key, None)
        )

        for first_next_last_count in range(3):

            #changes at each attempt

            audio_clip_generic_status_name = ''
            attempts_left = 0

            if first_next_last_count == 0:

                audio_clip_generic_status_name = 'processing_pending'
                attempts_left = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS

            elif first_next_last_count == 1:

                audio_clip_generic_status_name = 'processing_failed'
                attempts_left = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1

            elif first_next_last_count == 2:

                audio_clip_generic_status_name = 'processing_failed'
                attempts_left = 1

            #see how cache reconstructs itself

            #for-loop is to check how logic guarantees cache is correct, from outermost to innermost cache
            #loop_count 0, completely no cache
            #loop_count 1, has user cache
            #loop_count 2, has user cache + processing object
            for loop_count in range(3):

                sample_event_0 = EventsFactory(
                    event_created_by = target_user,
                    event_generic_status_generic_status_name = 'processing',
                )

                sample_audio_clip_0 = AudioClipsFactory(
                    audio_clip_user=target_user,
                    audio_clip_audio_clip_role_audio_clip_role_name='originator',
                    audio_clip_event=sample_event_0,
                    audio_clip_generic_status_generic_status_name=audio_clip_generic_status_name,
                    audio_clip_audio_file=self.unprocessed_object_key,
                )

                sample_audio_clip_metric_0 = AudioClipMetricsFactory(
                    audio_clip_metric_audio_clip=sample_audio_clip_0,
                )

                #set cache

                target_cache = None

                if loop_count > 0:

                    target_cache = CreateAudioClips.get_default_processing_cache_per_user()

                    cache.set(target_cache_key, target_cache)

                if loop_count > 1:

                    target_cache['processings'].update({
                        str(sample_audio_clip_0.id): CreateAudioClips.get_default_processing_object(
                            event=sample_event_0,
                            audio_clip=sample_audio_clip_0,
                        ),
                    })

                    target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = attempts_left
                    target_cache['processings'][str(sample_audio_clip_0.id)]['status'] = sample_audio_clip_0.generic_status.generic_status_name

                    cache.set(target_cache_key, target_cache)

                #proceed

                data = {
                    'audio_clip_id': sample_audio_clip_0.id,
                }

                request = self.client.post(reverse('create_events_process_api'), data)
                response_data = get_response_data(request)

                self.assertEqual(request.status_code, 200)

                sample_event_0.refresh_from_db()
                sample_audio_clip_0.refresh_from_db()

                #has cache but no processing object on normalise success
                #frontend uses last version of cache to check for completion

                target_cache = cache.get(target_cache_key, None)

                self.assertIsNotNone(target_cache)
                self.assertFalse(str(sample_audio_clip_0.id) in target_cache['processings'])

                #reset
                cache.set(target_cache_key, None)

                self.assertEqual(
                    sample_audio_clip_0.audio_file,
                    self.processed_object_key
                )
                self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
                self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'ok')

                #don't evaluate actual value, as it is always -1 in test, but has late -1 in prod due to the nature of task queue
                self.assertTrue('attempts_left' in response_data)


    #consecutive means the rows can be reused to repeatedly fail attempts
    def test_create_events__process__consecutive__first_next_last_attempts_failed(self):

        #since cache uses user.id, always create new user for every test case to ensure cache isolation
        target_user = self.create_user()

        self.login(target_user)

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=target_user.id,
        )

        #must not exist first
        self.assertIsNone(
            cache.get(target_cache_key, None)
        )

        sample_event_0 = EventsFactory(
            event_created_by = target_user,
            event_generic_status_generic_status_name = 'processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=target_user,
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing_pending',
            audio_clip_audio_file=self.faulty_audio_file_unprocessed_object_key_0,
        )

        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        #first and next attempts
        for loop_count in range(2):

            #proceed
    
            data = {
                'audio_clip_id': sample_audio_clip_0.id,
            }
    
            request = self.client.post(reverse('create_events_process_api'), data)
            response_data = get_response_data(request)
    
            self.assertEqual(request.status_code, 200)

            sample_event_0.refresh_from_db()
            sample_audio_clip_0.refresh_from_db()
    
            #has cache and processing object on normalise failure
            #frontend uses last version of cache to check for completion

            target_cache = cache.get(target_cache_key, None)

            self.assertIsNotNone(target_cache)
            self.assertTrue(str(sample_audio_clip_0.id) in target_cache['processings'])
            self.assertEqual(
                target_cache['processings'][str(sample_audio_clip_0.id)]['status'],
                sample_audio_clip_0.generic_status.generic_status_name
            )
            self.assertEqual(sample_event_0.generic_status.generic_status_name, 'processing')
            self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'processing_failed')
            self.assertEqual(
                sample_audio_clip_0.audio_file,
                self.faulty_audio_file_unprocessed_object_key_0
            )
            self.assertEqual(
                target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'],
                settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - (loop_count + 1)
            )

            #don't evaluate actual value, as it is always -1 in test, but has late -1 in prod due to the nature of task queue
            self.assertTrue('attempts_left' in response_data)

        #last attempt

        target_cache = cache.get(target_cache_key, None)
        target_cache['processings'][str(sample_audio_clip_0.id)]['attempts_left'] = 1
        cache.set(target_cache_key, target_cache)

        #proceed
    
        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }
    
        request = self.client.post(reverse('create_events_process_api'), data)
        response_data = get_response_data(request)
    
        self.assertEqual(request.status_code, 200)

        sample_event_0.refresh_from_db()
        sample_audio_clip_0.refresh_from_db()
    
        #has cache and processing object on normalise failure
        #frontend uses last version of cache to check for completion

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertFalse(str(sample_audio_clip_0.id) in target_cache['processings'])
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'deleted')
        self.assertEqual(sample_audio_clip_0.generic_status.generic_status_name, 'processing_max_attempts_reached')
        self.assertEqual(
            sample_audio_clip_0.audio_file,
            self.faulty_audio_file_unprocessed_object_key_0
        )

        #future attempts will be 404

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }
    
        request = self.client.post(reverse('create_events_process_api'), data)
        response_data = get_response_data(request)
    
        self.assertEqual(request.status_code, 404)


    def test_create_replies__process__not_consecutive_first_next_last_attempts_ok(self):

        #since cache uses user.id, always create new user for every test case to ensure cache isolation
        target_user = self.create_user()

        self.login(target_user)

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=target_user.id,
        )

        #must not exist first
        self.assertIsNone(
            cache.get(target_cache_key, None)
        )

        for first_next_last_count in range(3):

            #changes at each attempt

            audio_clip_generic_status_name = ''
            attempts_left = 0

            if first_next_last_count == 0:

                audio_clip_generic_status_name = 'processing_pending'
                attempts_left = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS

            elif first_next_last_count == 1:

                audio_clip_generic_status_name = 'processing_failed'
                attempts_left = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1

            elif first_next_last_count == 2:

                audio_clip_generic_status_name = 'processing_failed'
                attempts_left = 1

            #see how cache reconstructs itself

            #for-loop is to check how logic guarantees cache is correct, from outermost to innermost cache
            #loop_count 0, completely no cache
            #loop_count 1, has user cache
            #loop_count 2, has user cache + processing object
            for loop_count in range(3):

                sample_event_0 = EventsFactory(
                    event_created_by = target_user,
                    event_generic_status_generic_status_name = 'incomplete',
                )

                sample_audio_clip_0 = AudioClipsFactory(
                    audio_clip_user=target_user,
                    audio_clip_audio_clip_role_audio_clip_role_name='originator',
                    audio_clip_event=sample_event_0,
                    audio_clip_generic_status_generic_status_name='ok',
                    audio_clip_audio_file=self.processed_object_key,
                )
                sample_audio_clip_metric_0 = AudioClipMetricsFactory(
                    audio_clip_metric_audio_clip=sample_audio_clip_0,
                )

                sample_user_event_0 = self.create_user_event(
                    target_user.id,
                    sample_event_0.id,
                    when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
                )

                sample_event_reply_queue_0 = self.create_event_reply_queue(
                    event_id=sample_event_0.id,
                    locked_for_user_id=target_user.id,
                    is_replying=True,
                    when_locked=(get_datetime_now() - timedelta(seconds=0))
                )

                sample_audio_clip_1 = AudioClipsFactory(
                    audio_clip_user=target_user,
                    audio_clip_audio_clip_role_audio_clip_role_name='responder',
                    audio_clip_event=sample_event_0,
                    audio_clip_generic_status_generic_status_name=audio_clip_generic_status_name,
                    audio_clip_audio_file=self.unprocessed_object_key,
                )
                sample_audio_clip_metric_1 = AudioClipMetricsFactory(
                    audio_clip_metric_audio_clip=sample_audio_clip_1,
                )

                #set cache

                target_cache = None

                if loop_count > 0:

                    target_cache = CreateAudioClips.get_default_processing_cache_per_user()

                    cache.set(target_cache_key, target_cache)

                if loop_count > 1:

                    target_cache['processings'].update({
                        str(sample_audio_clip_1.id): CreateAudioClips.get_default_processing_object(
                            event=sample_event_0,
                            audio_clip=sample_audio_clip_1,
                        ),
                    })

                    target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] = attempts_left
                    target_cache['processings'][str(sample_audio_clip_1.id)]['status'] = sample_audio_clip_1.generic_status.generic_status_name

                    cache.set(target_cache_key, target_cache)

                #proceed

                data = {
                    'audio_clip_id': sample_audio_clip_1.id,
                }

                request = self.client.post(reverse('create_replies_process_api'), data)
                response_data = get_response_data(request)

                self.assertEqual(request.status_code, 200)

                sample_event_0.refresh_from_db()
                sample_audio_clip_1.refresh_from_db()

                #has cache but no processing object on normalise success
                #frontend uses last version of cache to check for completion

                target_cache = cache.get(target_cache_key, None)

                self.assertIsNotNone(target_cache)
                self.assertFalse(str(sample_audio_clip_1.id) in target_cache['processings'])

                #reset
                cache.set(target_cache_key, None)

                self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())
                self.assertEqual(
                    sample_audio_clip_1.audio_file,
                    self.processed_object_key
                )
                self.assertEqual(sample_event_0.generic_status.generic_status_name, 'completed')
                self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'ok')

                #don't evaluate actual value, as it is always -1 in test, but has late -1 in prod due to the nature of task queue
                self.assertTrue('attempts_left' in response_data)


    def test_create_replies__process__consecutive__first_next_last_attempts_failed(self):

        #since cache uses user.id, always create new user for every test case to ensure cache isolation
        target_user = self.create_user()

        self.login(target_user)

        target_cache_key = CreateAudioClips.determine_processing_cache_key(
            user_id=target_user.id,
        )

        #must not exist first
        self.assertIsNone(
            cache.get(target_cache_key, None)
        )

        sample_event_0 = EventsFactory(
            event_created_by = target_user,
            event_generic_status_generic_status_name = 'incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user=target_user,
            audio_clip_audio_clip_role_audio_clip_role_name='originator',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='ok',
            audio_clip_audio_file=self.processed_object_key,
        )
        sample_audio_clip_metric_0 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_0,
        )

        sample_user_event_0 = self.create_user_event(
            target_user.id,
            sample_event_0.id,
            when_excluded_for_reply=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_event_reply_queue_0 = self.create_event_reply_queue(
            event_id=sample_event_0.id,
            locked_for_user_id=target_user.id,
            is_replying=True,
            when_locked=(get_datetime_now() - timedelta(seconds=0))
        )

        sample_audio_clip_1 = AudioClipsFactory(
            audio_clip_user=target_user,
            audio_clip_audio_clip_role_audio_clip_role_name='responder',
            audio_clip_event=sample_event_0,
            audio_clip_generic_status_generic_status_name='processing_pending',
            audio_clip_audio_file=self.faulty_audio_file_unprocessed_object_key_0,
        )
        sample_audio_clip_metric_1 = AudioClipMetricsFactory(
            audio_clip_metric_audio_clip=sample_audio_clip_1,
        )

        #first and next attempts
        for loop_count in range(2):

            #proceed
    
            data = {
                'audio_clip_id': sample_audio_clip_1.id,
            }
    
            request = self.client.post(reverse('create_replies_process_api'), data)
            response_data = get_response_data(request)
    
            self.assertEqual(request.status_code, 200)

            sample_event_0.refresh_from_db()
            sample_audio_clip_1.refresh_from_db()
    
            #has cache and processing object on normalise failure
            #frontend uses last version of cache to check for completion

            target_cache = cache.get(target_cache_key, None)

            self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'processing_failed')
            self.assertEqual(
                sample_audio_clip_1.audio_file,
                self.faulty_audio_file_unprocessed_object_key_0
            )

            self.assertIsNotNone(target_cache)
            self.assertTrue(str(sample_audio_clip_1.id) in target_cache['processings'])
            self.assertEqual(
                target_cache['processings'][str(sample_audio_clip_1.id)]['status'],
                sample_audio_clip_1.generic_status.generic_status_name
            )

            #important part
            self.assertEqual(
                target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'],
                settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - (loop_count + 1)
            )

            #don't evaluate actual value, as it is always -1 in test, but has late -1 in prod due to the nature of task queue
            self.assertTrue('attempts_left' in response_data)

        #last attempt

        target_cache = cache.get(target_cache_key, None)
        target_cache['processings'][str(sample_audio_clip_1.id)]['attempts_left'] = 1
        cache.set(target_cache_key, target_cache)

        #proceed
    
        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }
    
        request = self.client.post(reverse('create_replies_process_api'), data)
        response_data = get_response_data(request)
    
        self.assertEqual(request.status_code, 200)

        sample_event_0.refresh_from_db()
        sample_audio_clip_1.refresh_from_db()
    
        #has cache and processing object on normalise failure
        #frontend uses last version of cache to check for completion

        target_cache = cache.get(target_cache_key, None)

        self.assertIsNotNone(target_cache)
        self.assertFalse(str(sample_audio_clip_1.id) in target_cache['processings'])
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')
        self.assertEqual(sample_audio_clip_1.generic_status.generic_status_name, 'processing_max_attempts_reached')
        self.assertFalse(EventReplyQueues.objects.filter(pk=sample_event_reply_queue_0.id).exists())

        self.assertEqual(
            sample_audio_clip_1.audio_file,
            self.faulty_audio_file_unprocessed_object_key_0
        )

        #future attempts will be 404

        data = {
            'audio_clip_id': sample_audio_clip_1.id,
        }
    
        request = self.client.post(reverse('create_replies_process_api'), data)
        response_data = get_response_data(request)
    
        self.assertEqual(request.status_code, 404)



































































