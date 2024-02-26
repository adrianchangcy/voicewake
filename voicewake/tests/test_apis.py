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

#py packages
import io
import json
from datetime import datetime, timezone
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

#AWS
import boto3
from botocore.exceptions import ClientError

#apps
from voicewake.services import *
from voicewake.models import *
from voicewake.tasks import *
from voicewake.factories import *
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
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'voicewake/tests'),
)
class AWS_TestCase(TestCase):


    @classmethod
    def setUpTestData(cls):

        #uses production bucket
        cls.upload_folder_path = 'test/'

        test_file_prefix = os.path.join(settings.BASE_DIR, 'voicewake/tests/test_file_samples/')

        #files for test
        cls.test_files = {
            'audio_not_mp3': {
                'file': test_file_prefix + 'audio_not_mp3.wav',
                'expected_status_code': 400,
            },
            'audio_ok_1': {
                'file': test_file_prefix + 'audio_ok_1.mp3',
                'expected_status_code': 200,
            },
            'audio_ok_2': {
                'file': test_file_prefix + 'audio_ok_2.mp3',
                'expected_status_code': 200,
            },
            'audio_too_large': {
                'file': test_file_prefix + 'audio_too_large.mp3',
                'expected_status_code': 400,
            },
            'not_audio': {
                'file': test_file_prefix + 'not_audio.txt',
                'expected_status_code': 400,
            },
            'txt_as_fake_mp3': {
                'file': test_file_prefix + 'txt_as_fake_mp3.mp3',
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

        upload_key = 'test/test_upload_and_delete_ok' + '.mp3'

        s3_wrapper_class = S3PostWrapper(
            is_ec2=False,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B'],
            url_expiry_s=os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S'],
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        upload_info = s3_wrapper_class.generate_presigned_post_url(upload_key)

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

        upload_key = 'test/test_upload_file_too_large' + '.mp3'

        s3_wrapper_class = S3PostWrapper(
            is_ec2=False,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B'],
            url_expiry_s=os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S'],
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        upload_info = s3_wrapper_class.generate_presigned_post_url(upload_key)

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


    def test_upload_policy_does_not_validate_payload(self):

        #policy only validates the file extension of key
        #policy does not validate actual payload
        #so key of .mp3, with payload of .wav, will still return 204

        upload_key = 'test/test_upload_wrong_file_extension' + '.mp3'

        s3_wrapper_class = S3PostWrapper(
            is_ec2=False,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B'],
            url_expiry_s=os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S'],
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        upload_info = s3_wrapper_class.generate_presigned_post_url(upload_key)

        upload_url = upload_info['url']
        upload_fields = upload_info['fields']

        try:

            print(self.test_files['audio_not_mp3']['file'])

            response = self.s3_post_upload(upload_url, upload_fields, self.test_files['audio_not_mp3']['file'])

            print(response)

            #if unexpectedly no error, delete stored file

            response = s3_wrapper_class.delete_object(upload_key)

            self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 204)

            raise ValueError('Unexpected upload success.')

        except Exception as e:

            print(e)


    def test_upload_multiple_same_file_to_same_url(self):

        upload_key = 'test/test_upload_more_files_same_url' + '.mp3'

        s3_wrapper_class = S3PostWrapper(
            is_ec2=False,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B'],
            url_expiry_s=os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S'],
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        upload_info = s3_wrapper_class.generate_presigned_post_url(upload_key)

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

        upload_key = 'test/test_lambda' + '.mp3'

        s3_wrapper_class = S3PostWrapper(
            is_ec2=False,
            allowed_unprocessed_file_extensions=settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            s3_audio_file_max_size_b=os.environ['AWS_S3_AUDIO_FILE_MAX_SIZE_B'],
            url_expiry_s=os.environ['AWS_S3_UPLOAD_URL_EXPIRY_S'],
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        if s3_wrapper_class.check_object_exists(upload_key) is False:

            upload_info = s3_wrapper_class.generate_presigned_post_url(upload_key)

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
            FunctionName='normalise_audio_clips',
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


    def test_pass_none_to_use_instance_credentials(self):

        #do this at lambda
        #AWS_...=None
        pass


    def test_production_bucket_cors_policy_rejected(self):

        pass






    def test_lambda_from_local(self):

        #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda/client/invoke.html#

        lambda_client = boto3.client(
            service_name='lambda',
            region_name=os.environ['AWS_S3_REGION_NAME'],
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        lambda_payload = json.dumps({"name":"name","age":"age"})

        result = lambda_client.invoke(
            FunctionName=os.environ['AWS_LAMBDA_TEST_ARN'],
            InvocationType='RequestResponse',
            Payload=lambda_payload,
        )

        print(result)

        #at Lambda, use {}.get() for keys to prevent error when not found


    def test_lambda_ffprobe_from_local(self):

        def lambda_handler(event, context):

            audio_file = event.get('audio_file')

            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format',  #if you want only some keys, do format=duration, no difference though
                    '-show_streams',
                    '-select_streams', 'a',
                    '-of', 'json',
                    '-i', 'pipe:0'
                ],
                input=audio_file.read(),
                check=True,
                capture_output=True,
                timeout=10
            )

            audio_file.seek(0)

            audio_file_info = json.loads(result.stdout)

            return {
                'statusCode': 200,
                'body': json.dumps({
                    'audio_file_info': audio_file_info,
                    'audio_file': audio_file
                }),
            }

        lambda_client = boto3.client(
            service_name='lambda',
            region_name=os.environ['AWS_S3_REGION_NAME'],
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        #example file
        audio_file_full_path = os.path.join(settings.BASE_DIR, 'voicewake/tests/test_file_samples/audio_can_overwrite.mp3')

        #automate args
        file_extension = audio_file_full_path.split(".", -1)[-1]
        temporary_audio_file_name = 'new_recording' + '.' + file_extension
        content_type = 'audio/' + file_extension

        #simulate InMemoryUploadedFile
        audio_file_in_memory = InMemoryUploadedFile(
            io.FileIO(audio_file_full_path, mode="rb+"),
            'FileField',
            temporary_audio_file_name,
            content_type,
            os.path.getsize(audio_file_full_path),
            None
        )

        lambda_payload = json.dumps({
            'audio_file': audio_file_in_memory
        })

        result = lambda_client.invoke(
            FunctionName=os.environ['AWS_LAMBDA_TEST_ARN'],
            InvocationType='RequestResponse',
            Payload=lambda_payload,
        )

        print(result)


    def get_keys_from_ec2_in_prod(self):

        session = boto3.Session(region_name=os.environ['AWS_S3_REGION_NAME'])
        credentials = session.get_credentials()
        credentials = credentials.get_frozen_credentials()
        ACCESS_KEY_ID = credentials.access_key
        ACCESS_SECRET_KEY = credentials.secret_key 



@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'voicewake/tests'),
)
class Random_TestCase(TestCase):

    def test_random(self):

        pass



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
            'voicewake/tests/test_file_samples/audio_ok_1.mp3'
        )

        #where to overwrite file
        cls.overwrite_audio_file_full_path = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/test_file_samples/audio_can_overwrite.mp3'
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


    def test_ffmpeg(self):

        #should have webm/opus and mp4/__ files for test, but too lazy for now
        #webm/opus works
        #https://dirask.com/posts/JavaScript-supported-Audio-Video-MIME-Types-by-MediaRecorder-Chrome-and-Firefox-jERn81

        # audio_file = 'audio-clips/year_2023/month_7/day_21/user_id_1/e_13.webm'

        handle_audio_file_class = AWSLambdaNormaliseAudioClips(
            is_lambda=False,
            region_name=os.environ['AWS_S3_REGION_NAME'],
            unprocessed_bucket_name=os.environ['AWS_S3_UGC_UNPROCESSED_BUCKET_NAME'],
            processed_bucket_name=os.environ['AWS_S3_MEDIA_BUCKET_NAME'],
            aws_access_key_id=os.environ['AWS_S3_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_S3_SECRET_ACCESS_KEY'],
        )

        handle_audio_file_class.test_retrieve_unprocessed_audio_file_local(
            self.source_audio_file_full_path
        )

        handle_audio_file_class.prepare_info_before_normalise()

        #get duration by simply converting file here, then get duration
        #then can get peaks

        handle_audio_file_class.normalise_and_overwrite_audio_file()

        handle_audio_file_class.get_peaks_by_buckets()

        new_peaks = handle_audio_file_class.get_peaks_by_buckets()

        #to compare old and new peaks, must manually ensure duration exists first
        #in production, this isn't necessary, and would be redundant

        print(new_peaks)



#not yet adjusted to use FactoryBoy
@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'voicewake/tests'),
)
class CoreProcess_TestCase(TestCase):

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

        #audio file
        cls.audio_file_full_path = os.path.join(settings.BASE_DIR, 'voicewake/tests/test_file_samples/audio_can_overwrite.mp3')
        cls.audio_file = open(cls.audio_file_full_path, 'rb')
        cls.audio_file = SimpleUploadedFile(cls.audio_file.name, cls.audio_file.read(), 'audio/mp3')

        #bad file
        cls.bad_file_full_path = os.path.join(settings.BASE_DIR, 'voicewake/tests/test_file_samples/not_audio.txt')
        cls.bad_file = open(cls.bad_file_full_path, 'rb')
        cls.bad_file = SimpleUploadedFile(cls.bad_file.name, cls.bad_file.read(), 'audio/mp3')


    @classmethod
    def tearDownClass(cls):

        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, 'audio_clips'), ignore_errors=True)

        super().tearDownClass()


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


    def test_create_event__upload__ok(self):

        self.login(self.users[0])

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 201)

        #check data

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)['data']

        self.assertTrue('upload_url' in result_data)
        self.assertTrue('upload_fields' in result_data)
        self.assertTrue('audio_clip_id' in result_data)

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

        self.assertEqual(request.status_code, 404)


    def test_create_event__upload__not_idempotent_ok(self):

        self.login(self.users[0])

        #first request, new records

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 201)

        #second request, new records

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 201)

        #check data

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)['data']

        self.assertTrue('upload_url' in result_data)
        self.assertTrue('upload_fields' in result_data)
        self.assertTrue('audio_clip_id' in result_data)

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

            self.assertEqual(request.status_code, 404)

        audio_clips = AudioClips.objects.all()

        for audio_clip in audio_clips:

            self.assertEqual(audio_clip.generic_status.generic_status_name, 'processing')
            self.assertEqual(audio_clip.user_id, self.users[0].id)
            self.assertEqual(audio_clip.audio_clip_tone_id, data['audio_clip_tone_id'])
            self.assertGreater(len(audio_clip.audio_file), 0)
            self.assertEqual(audio_clip.audio_duration_s, 0)
            self.assertEqual(len(audio_clip.audio_volume_peaks), 0)


    def test_create_event__upload__daily_limit_reached(self):

        #time-based
        #AudioClips.GenericStatuses.generic_status_name is not relevant
        #only checks against AudioClips

        self.login(self.users[0])

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
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
                'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
            }

            request = self.client.post(reverse('create_events_upload_api'), data)

            self.assertEqual(request.status_code, 400)

            #generic_status_name = 'ok'

            target_audio_clip.generic_status = GenericStatuses.objects.get(generic_status_name='ok')
            target_audio_clip.save()

            data={
                'event_name': 'yolo',
                'audio_clip_tone_id': 1,
                'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
            }

            request = self.client.post(reverse('create_events_upload_api'), data)

            self.assertEqual(request.status_code, 400)

            #is_banned=True

            target_audio_clip.is_banned = True
            target_audio_clip.save()

            data={
                'event_name': 'yolo',
                'audio_clip_tone_id': 1,
                'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
            }

            request = self.client.post(reverse('create_events_upload_api'), data)

            self.assertEqual(request.status_code, 400)


    def test_create_event__upload__missing_args(self):

        self.login(self.users[0])

        data={
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 400)

        data={
            'event_name': 'yolo',
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 400)

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 1,
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 400)


    def test_create_event__upload__faulty_args(self):

        self.login(self.users[0])

        data={
            'event_name': '',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 400)

        data={
            'event_name': '    ',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 400)

        data={
            'event_name': 'ha   ha',
            'audio_clip_tone_id': 1,
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 201)

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': '1',  #fine
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
        }

        request = self.client.post(reverse('create_events_upload_api'), data)

        self.assertEqual(request.status_code, 201)

        data={
            'event_name': 'yolo',
            'audio_clip_tone_id': 'b',
            'recorded_file_extension': settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
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


    def test_create_event__regenerate_upload_url__ok(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_file_object_key = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 200)


    def test_create_event__regenerate_upload_url__resubmit_ok(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_file_object_key = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
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


    def test_create_event__regenerate_upload_url__already_processed(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_file_object_key = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_PROCESSED_FILE_TYPE,
            audio_clip_generic_status_generic_status_name = 'ok',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 404)


    def test_create_event__regenerate_upload_url__no_rows(self):

        self.login(self.users[0])

        #proceed

        data = {
            'audio_clip_id': 1,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 404)


    def test_create_event__regenerate_upload_url__only_own_rows_allowed(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[1],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_file_object_key = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 404)


    def test_create_event__regenerate_upload_url__missing_args(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_file_object_key = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {}

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        print_function_name(request.content)
        self.assertEqual(request.status_code, 400)


    def test_create_event__regenerate_upload_url__faulty_args(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_file_object_key = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {
            'audio_clip_id': '1a',
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 400)

        data = {
            'audio_clip_id': '     1     ',
        }

        request = self.client.post(reverse('create_events_regenerate_upload_url_api'), data)

        self.assertEqual(request.status_code, 200)









    def test_create_event__process__ok(self):

        #involves AWS Lambda
        #best to do subsequent real-world requests

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )
        pass


    def test_create_event__process__resubmit_ok(self):

        #involves AWS Lambda
        #best to do subsequent real-world requests

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )
        pass









    def test_create_event__process__already_processed(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='incomplete',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_file_object_key = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_PROCESSED_FILE_TYPE,
            audio_clip_generic_status_generic_status_name = 'ok',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 400)


    def test_create_event__process__nothing_to_process(self):

        self.login(self.users[0])

        #proceed

        data = {
            'audio_clip_id': 1,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 400)


    def test_create_event__process__only_own_rows_allowed(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[1],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[1],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_file_object_key = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_UNPROCESSED_FILE_TYPES[0],
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {
            'audio_clip_id': sample_audio_clip_0.id,
        }

        request = self.client.post(reverse('create_events_process_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 400)


    def test_create_event__process__missing_args(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_file_object_key = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_PROCESSED_FILE_TYPE,
            audio_clip_generic_status_generic_status_name = 'processing',
        )

        #proceed

        data = {}

        request = self.client.post(reverse('create_events_process_api'), data)

        print(request.content)
        self.assertEqual(request.status_code, 400)


    def test_create_event__process__faulty_args(self):

        self.login(self.users[0])

        sample_event_0 = EventsFactory(
            event_created_by=self.users[0],
            event_generic_status_generic_status_name='processing',
        )

        sample_audio_clip_0 = AudioClipsFactory(
            audio_clip_user = self.users[0],
            audio_clip_audio_clip_role_audio_clip_role_name = 'originator',
            audio_clip_event = sample_event_0,
            audio_file_object_key = 'yolofolder/yolofile.' + settings.AUDIO_CLIP_PROCESSED_FILE_TYPE,
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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(
            EventReplyQueues.objects.filter(
                locked_for_user=self.users[1], event_id=sample_event_1.id, is_replying=False
            ).exists()
        )
        self.assertEqual(result_data['event_reply_daily_limit_reached'], True)
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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)
        result_data = result_data['data'][0]

        self.assertTrue('event' in result_data and type(result_data['event']) == dict)
        self.assertTrue('originator' in result_data and len(result_data['originator']) == 1)
        self.assertTrue('responder' in result_data and len(result_data['responder']) == 0)
        self.assertTrue('event_reply_queue' in result_data and type(result_data['event_reply_queue']) == dict)

        event_reply_queue = EventReplyQueues.objects.first()
        user_event = UserEvents.objects.first()

        self.assertTrue(result_data['event_reply_queue']['when_locked'] is not None)
        self.assertEqual(result_data['event_reply_queue']['is_replying'], event_reply_queue.is_replying)
        self.assertEqual(result_data['event']['id'], event_reply_queue.event_id)
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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)
        result_data = result_data['data'][0]

        self.assertTrue('event' in result_data and type(result_data['event']) == dict)
        self.assertTrue('originator' in result_data and len(result_data['originator']) == 1)
        self.assertTrue('responder' in result_data and len(result_data['responder']) == 0)
        self.assertTrue('event_reply_queue' in result_data and type(result_data['event_reply_queue']) == dict)

        event_reply_queue = EventReplyQueues.objects.first()
        user_event = UserEvents.objects.first()

        self.assertTrue(result_data['event_reply_queue']['when_locked'] is not None)
        self.assertEqual(result_data['event_reply_queue']['is_replying'], event_reply_queue.is_replying)
        self.assertEqual(result_data['event']['id'], event_reply_queue.event_id)
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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)
        result_data = result_data['data']

        self.assertEqual(result_data, [])
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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)
        result_data = result_data['data']

        self.assertEqual(result_data, [])
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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)
        result_data = result_data['data']

        self.assertEqual(len(result_data), 0)
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(UserEvents.objects.all().count(), 0)


    def test_list_reply_choices_has_something_locked_no_unlock(self):

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(sample_event_0.id, result_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 1)
        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertEqual(EventReplyQueues.objects.first().id, sample_event_reply_queue_0.id)
        self.assertEqual(EventReplyQueues.objects.first().when_locked, sample_event_reply_queue_0.when_locked)


    def test_list_reply_choices_has_something_locked_has_unlock(self):

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=result_data['data'][0]['event']['id'])

        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertNotEqual(EventReplyQueues.objects.first().id, result_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 2)
        self.assertEqual(new_user_event.event_id, sample_event_1.id)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)
        self.assertNotEqual(EventReplyQueues.objects.first().when_locked, sample_event_reply_queue_0.when_locked)


    def test_list_reply_choices_has_something_locked_but_expired_no_unlock(self):

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=result_data['data'][0]['event']['id'])

        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertNotEqual(EventReplyQueues.objects.first().id, result_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 2)
        self.assertEqual(new_user_event.event_id, sample_event_1.id)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)


    def test_list_reply_choices_has_something_locked_but_expired_has_unlock(self):

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        new_user_event = UserEvents.objects.get(user=self.users[1], event_id=result_data['data'][0]['event']['id'])

        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertNotEqual(EventReplyQueues.objects.first().id, result_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 2)
        self.assertEqual(new_user_event.event_id, sample_event_1.id)
        self.assertIsNotNone(new_user_event.when_excluded_for_reply)


    def test_start_reply_ok(self):

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=sample_event_0.id)

        self.assertTrue(event_reply_queue.is_replying)
        self.assertEqual(result_data['data'][0]['event_id'], event_reply_queue.event_id)
        self.assertEqual(
            datetime.strptime(result_data['data'][0]['when_locked'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=ZoneInfo('UTC')),
            event_reply_queue.when_locked
        )
        self.assertEqual(result_data['data'][0]['is_replying'], event_reply_queue.is_replying)


    def test_start_reply_with_missing_args(self):

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=sample_event_0.id)

        self.assertFalse(event_reply_queue.is_replying)


    def test_start_reply_with_faulty_args(self):

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

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        event_reply_queue = EventReplyQueues.objects.get(locked_for_user=self.users[1], event_id=sample_event_0.id)

        self.assertFalse(event_reply_queue.is_replying)


    def test_list_new_event_with_started_reply_no_unlock(self):

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

        data = {'unlock_all_locked_events': False}

        request = self.client.post(reverse('list_event_reply_choices_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(sample_event_0.id, result_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 1)
        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertEqual(EventReplyQueues.objects.first().id, sample_event_reply_queue_0.id)


    def test_list_new_event_with_started_reply_has_unlock(self):

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertNotEqual(sample_event_0.id, result_data['data'][0]['event']['id'])
        self.assertEqual(UserEvents.objects.all().count(), 2)
        self.assertEqual(EventReplyQueues.objects.all().count(), 1)
        self.assertNotEqual(EventReplyQueues.objects.first().id, sample_event_reply_queue_0.id)


    def test_start_reply_but_never_queued(self):

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

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)


    def test_start_reply_but_expired(self):

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

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(result_data['can_retry'])
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(
            UserEvents.objects.filter(
                user=self.users[1],
                event_id=sample_event_0,
                when_excluded_for_reply__isnull=False
            ).count(),
            1
        )


    def test_start_reply_but_event_is_banned(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "deleted"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
            generic_status_name="deleted",
            is_banned=True,
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

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(result_data['can_retry'])
        self.assertEqual(EventReplyQueues.objects.all().count(), 0)
        self.assertEqual(
            UserEvents.objects.filter(
                user=self.users[1],
                event_id=sample_event_0,
                when_excluded_for_reply__isnull=False
            ).count(),
            1
        )


    def test_start_reply_for_someone_else(self):

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

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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



















def test_create_reply__upload__resubmit_deny(self):
    pass


def test_create_reply__upload__never_queued_for_it(self):
    pass


def test_create_reply__upload__not_locked_not_replying(self):
    pass


def test_create_reply__upload__is_locked_not_replying(self):
    pass


def test_create_reply__upload__is_locked_is_replying_ok(self):
    pass


def test_create_reply__upload__is_locked_is_replying_is_expired(self):
    pass


def test_create_reply__upload__event_is_banned(self):
    pass


def test_create_reply__upload__missing_args(self):
    pass


def test_create_reply__upload__faulty_args(self):
    pass













    def test_create_reply_ok(self):

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
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 201)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 2)
        self.assertEqual(
            AudioClips.objects.filter(
                user_id=self.users[1].id,
                event_id=sample_event_0.id,
                audio_clip_role__audio_clip_role_name='responder',
                audio_clip_tone=self.audio_clip_tone
            ).count(),
            1
        )


    def test_create_reply_with_missing_args(self):

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
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        data = {
            'event_id': sample_event_0.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': self.audio_clip_tone.id,
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_create_reply_with_faulty_args(self):

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
            'event_id': 99999,
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': 99999,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 404)
        print_function_name(request.content)

        data = {
            'event_id': sample_event_0.id,
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_bad_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_create_reply_but_never_queued_for_it(self):

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
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)


    def test_create_reply_locked_but_not_replying(self):

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
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertTrue(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)


    def test_create_reply_for_someone_else(self):

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
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertTrue(EventReplyQueues.objects.filter(locked_for_user=self.users[2], event_id=sample_event_0.id).exists())
        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)


    def test_create_reply_but_expired(self):

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
            when_locked=(get_datetime_now() - timedelta(seconds=(settings.EVENT_REPLY_MAX_DURATION_S * 2)))
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
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(result_data['can_retry'])
        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertEqual(AudioClips.objects.filter(user_id=self.users[1].id).count(), 0)
        self.assertEqual(UserEvents.objects.filter(user_id=self.users[1].id).count(), 1)
        sample_event_0.refresh_from_db()
        self.assertEqual(sample_event_0.generic_status.generic_status_name, 'incomplete')


    def test_create_reply_but_event_is_banned(self):

        #prepare data

        sample_event_0 = self.create_event(
            self.users[0],
            "deleted"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
            generic_status_name="deleted",
            is_banned=True,
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
            'audio_clip_tone_id': self.audio_clip_tone.id,
            'audio_file': self.get_audio_file(),
        }

        request = self.client.post(reverse('create_replies_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(result_data['can_retry'])
        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertEqual(AudioClips.objects.filter(user_id=self.users[1].id).count(), 0)
        self.assertEqual(UserEvents.objects.filter(user_id=self.users[1].id).count(), 1)


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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        self.assertEqual(request.status_code, 400)
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

        self.assertEqual(request.status_code, 400)
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

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())


    def test_cancel_reply_for_someone_else(self):

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

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
            generic_status_name="deleted",
            is_banned=True,
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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertFalse(EventReplyQueues.objects.filter(locked_for_user=self.users[1], event_id=sample_event_0.id).exists())
        self.assertEqual(Events.objects.count(), 1)
        self.assertEqual(AudioClips.objects.count(), 1)
        self.assertTrue(UserEvents.objects.filter(user=self.users[1], event_id=sample_event_0.id).exists())














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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertIsNone(audio_clip_report.last_evaluated)


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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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
            audio_clip_id=sample_audio_clip_0.id
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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertIsNone(audio_clip_report.last_evaluated)


    def test_create_audio_clip_report_already_banned(self):

        #prepare

        sample_event_0 = self.create_event(
            self.users[0],
            "incomplete"
        )

        sample_audio_clip_0 = self.create_audio_clip(
            self.users[0].id,
            sample_event_0.id,
            "originator",
            is_banned=True,
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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        audio_clip_report = AudioClipReports.objects.first()

        self.assertEqual(AudioClipReports.objects.all().count(), 1)
        self.assertEqual(audio_clip_report.audio_clip_id, sample_audio_clip_0.id)
        self.assertIsNone(audio_clip_report.last_evaluated)


    def test_create_user_block_ok(self):

        self.login(self.users[1])

        data = {
            'username': self.users[0].username,
            'to_block': True
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(UserBlocks.objects.all().count(), 1)


    def test_create_user_block_missing_args(self):

        self.login(self.users[1])

        #start

        data = {
            'username': self.users[0].username,
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        #200 because bool defaults to False when not passed
        self.assertEqual(request.status_code, 200)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(UserBlocks.objects.all().count(), 0)

        #start

        data = {
            'to_block': True,
        }

        request = self.client.post(reverse('user_blocks_api'), data)

        self.assertEqual(request.status_code, 400)
        print_function_name(request.content)

        #check

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(UserBlocks.objects.all().count(), 0)


    def test_create_user_block_faulty_args(self):

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(UserBlocks.objects.all().count(), 0)


    def test_create_user_block_unblock_ok(self):

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

        self.assertEqual(UserBlocks.objects.all().count(), 0)


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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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

        result_data = (bytes(request.content).decode())
        result_data = json.loads(result_data)

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



















































