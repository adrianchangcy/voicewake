from django.http import JsonResponse, QueryDict
from django.db.models import Case, Value, When, Sum, Q, F, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.utils.cache import patch_cache_control
from django.utils.decorators import method_decorator
from django.db.models import Prefetch
from django.db.utils import IntegrityError
from django.urls import reverse

#auth
from django.contrib.auth import get_user_model, login, logout
from django.views.decorators.csrf import csrf_protect

#DRF, class-based views
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets, generics
    #ModelViewSet has: list, create, retrieve, update, partial_update, destroy
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

#mixins
# from django.contrib.auth.mixins import PermissionRequiredMixin

#Python
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
import zoneinfo
import json
import time
import math
import random
import traceback
import io
from typing import Literal
from subprocess import CalledProcessError

#app files
from voicewake.models import *
from voicewake.serializers import *
from voicewake.services import *
import voicewake.decorators as app_decorators
from django.conf import settings

#specifically just for error handling
from psycopg.errors import UniqueViolation
from django.db.utils import IntegrityError



class TestAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = []
    current_context = ""


    def get(self, request, *args, **kwargs):



        return Response(
            data={
                'data': {},
                'message': 'testo'
            },
            status=status.HTTP_200_OK
        )









class AudioClipReportsAPI(generics.GenericAPIView):

    serializer_class = AudioClipReportsAPISerializer
    permission_classes = [IsAuthenticated]

    #no get() here, users don't have to see what audio_clips they've reported

    #user wants to report an audio_clip
    @method_decorator(app_decorators.deny_if_banned("response"))
    def post(self, request, *args, **kwargs):

        serializer = AudioClipReportsAPISerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_data = serializer.validated_data

        try:

            #get audio_clip
            target_audio_clip = AudioClips.objects.get(pk=new_data['audio_clip_id'])

        except AudioClips.DoesNotExist:

            return Response(
                data={
                    'message': 'Recording does not exist.',
                },
                status=status.HTTP_404_NOT_FOUND
            )

        #no need to check whether audio_clip belongs to user

        #check if already banned
        if target_audio_clip.is_banned is True:

            return Response(
                data={
                    'message': 'This recording has already been banned.',
                },
                status=status.HTTP_200_OK
            )

        #add report
        audio_clip_report, is_created = AudioClipReports.objects.get_or_create(audio_clip_id=new_data['audio_clip_id'])

        if is_created is False:

            audio_clip_report.last_reported = get_datetime_now()
            audio_clip_report.save()

        #for edge case where same user reports --> evaluated --> reports again,
        #no need to do anything, otherwise our cronjob can get overwhelmed

        return Response(
            data={
                'message': 'The recording is now queued for evaluation.',
            },
            status=status.HTTP_200_OK
        )



class UserBannedAudioClipsAPI(generics.GenericAPIView):

    serializer_class = AudioClipsSerializer
    permission_classes = [IsAuthenticated]

    #no post() here, cronjob does the banning


    def get_latest_banned_audio_clips(self, next_or_back:Literal['next', 'back'], cursor_token:str=''):

        #we could simply implement when_banned
        #but due to deadlines, there was no time available to retest BrowseEventsAPI
            #using when_banned did increase query time

        #this is sufficient, as long as:
            #being banned is the last possible step to trigger last_modified

        result = {
            'rows': [],
            'next_cursor_token': cursor_token,
            'back_cursor_token': cursor_token,
        }

        #only show when user is still banned

        if self.request.user.banned_until is None:

            return result

        #handle cursor token

        decoded_cursor_token = {}
        cursor_params = []

        if cursor_token != '':

            try:

                #get audio_clips.last_modified, audio_clips.id
                decoded_cursor_token = decode_cursor_token(cursor_token)

                cursor_params = [
                    decoded_cursor_token['last_modified'],
                    decoded_cursor_token['id'], decoded_cursor_token['last_modified'],
                ]

            except:

                raise custom_error(
                    ValueError,
                    user_message="Unable to fetch content due to faulty cursor token.",
                    dev_message="Token could not be decoded: " + cursor_token
                )

        #prepare adjustments based on cursor direction

        cursor_sql = ''

        if next_or_back == 'next':

            if len(decoded_cursor_token) > 0:

                cursor_sql = '''
                    AND (
                        audio_clips.last_modified <= %s
                        AND
                        (audio_clips.id < %s OR audio_clips.last_modified < %s)
                    )
                '''

        elif next_or_back == 'back':

            if len(decoded_cursor_token) > 0:

                cursor_sql = '''
                    AND (
                        audio_clips.last_modified >= %s
                        AND
                        (audio_clips.id > %s OR audio_clips.last_modified > %s)
                    )
                '''

        #proceed

        full_sql = '''
            SELECT * FROM audio_clips
            INNER JOIN generic_statuses ON audio_clips.generic_status_id = generic_statuses.id
            WHERE is_banned IS TRUE
            AND audio_clips.user_id = %s
            AND generic_statuses.generic_status_name = %s
            ''' + cursor_sql + '''
            ORDER BY audio_clips.last_modified DESC, audio_clips.id DESC
			LIMIT %s
        '''

        full_params = [
            self.request.user.id,
            'deleted',
        ] + cursor_params + [
            settings.LIST_AUDIO_CLIP_QUANTITY_PER_PAGE,
        ]

        #execute

        audio_clips = AudioClips.objects.prefetch_related(
            'audio_clip_role',
            'audio_clip_tone',
            'generic_status',
            'user',
        ).raw(
            full_sql,
            params=full_params
        )

        list(audio_clips)

        if len(audio_clips) == 0:

            return result
        
        result['rows'] = audio_clips

        #start preparing our cursor tokens

        result['back_cursor_token'] = encode_cursor_token({
            'last_modified': audio_clips[0].last_modified.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
            'id': audio_clips[0].id,
        })

        result['next_cursor_token'] = encode_cursor_token({
            'last_modified': audio_clips[-1].last_modified.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
            'id': audio_clips[-1].id,
        })

        return result


    def get(self, request, *args, **kwargs):

        serializer = UserBannedAudioClipsAPISerializer(data=kwargs, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        #continue

        result = self.get_latest_banned_audio_clips(
            new_data['next_or_back'],
            new_data['cursor_token'],
        )

        #prepare URLs

        current_url_splits = self.request.build_absolute_uri().split(new_data['next_or_back'], 1)

        next_url = current_url_splits[0] + "next"
        back_url = current_url_splits[0] + "back"

        if len(result['rows']) > 0:

            next_url += "/" + result['next_cursor_token']
            back_url += "/" + result['back_cursor_token']

        elif new_data['cursor_token'] != '':

            next_url += "/" + new_data['cursor_token']
            back_url += "/" + new_data['cursor_token']

        #prepare response

        serializer = AudioClipsSerializer(result['rows'], many=True)

        return Response(
            data={
                'next_url': next_url,
                'back_url': back_url,
                'message': '',
                'data': serializer.data,
            },
            status=status.HTTP_200_OK
        )



class UserBlocksAPI(generics.GenericAPIView):

    serializer_class = UserBlocksSerializer
    permission_classes = [IsAuthenticated]


    def get_latest_user_blocks(self, next_or_back:Literal['next', 'back'], cursor_token:str=''):

        #we could simply implement when_banned
        #but due to deadlines, there was no time available to retest BrowseEventsAPI
            #using when_banned did increase query time

        #this is sufficient, as long as:
            #being banned is the last possible step to trigger last_modified

        result = {
            'rows': [],
            'next_cursor_token': cursor_token,
            'back_cursor_token': cursor_token,
        }

        #handle cursor token

        decoded_cursor_token = {}
        cursor_params = []

        if cursor_token != '':

            try:

                #get audio_clips.last_modified, audio_clips.id
                decoded_cursor_token = decode_cursor_token(cursor_token)

                cursor_params = [
                    decoded_cursor_token['when_created'],
                    decoded_cursor_token['id'], decoded_cursor_token['when_created'],
                ]

            except:

                raise custom_error(
                    ValueError,
                    user_message="Unable to fetch content due to faulty cursor token.",
                    dev_message="Token could not be decoded: " + cursor_token
                )

        #prepare adjustments based on cursor direction

        cursor_sql = ''

        if next_or_back == 'next':

            if len(decoded_cursor_token) > 0:

                cursor_sql = '''
                    AND (
                        user_blocks.when_created <= %s
                        AND
                        (user_blocks.id < %s OR user_blocks.when_created < %s)
                    )
                '''

        elif next_or_back == 'back':

            if len(decoded_cursor_token) > 0:

                cursor_sql = '''
                    AND (
                        user_blocks.when_created >= %s
                        AND
                        (user_blocks.id > %s OR user_blocks.when_created > %s)
                    )
                '''

        #proceed

        full_sql = '''
            SELECT * FROM user_blocks
            WHERE user_id = %s
            ''' + cursor_sql + '''
            ORDER BY user_blocks.when_created DESC, user_blocks.id DESC
			LIMIT %s
        '''

        full_params = [
            self.request.user.id,
        ] + cursor_params + [
            settings.USER_BLOCK_QUANTITY_PER_PAGE,
        ]

        #execute

        user_blocks = UserBlocks.objects.prefetch_related(
            'user',
            'blocked_user',
        ).raw(
            full_sql,
            params=full_params
        )

        list(user_blocks)

        if len(user_blocks) == 0:

            return result
        
        result['rows'] = user_blocks

        #start preparing our cursor tokens

        result['back_cursor_token'] = encode_cursor_token({
            'when_created': user_blocks[0].when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
            'id': user_blocks[0].id,
        })

        result['next_cursor_token'] = encode_cursor_token({
            'when_created': user_blocks[-1].when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
            'id': user_blocks[-1].id,
        })

        return result


    def get(self, request, *args, **kwargs):

        serializer = GetUserBlocksAPISerializer(data=kwargs, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        #continue

        result = self.get_latest_user_blocks(
            new_data['next_or_back'],
            new_data['cursor_token'],
        )

        #prepare URLs

        current_url_splits = self.request.build_absolute_uri().split(new_data['next_or_back'], 1)

        next_url = current_url_splits[0] + "next"
        back_url = current_url_splits[0] + "back"

        if len(result['rows']) > 0:

            next_url += "/" + result['next_cursor_token']
            back_url += "/" + result['back_cursor_token']

        elif new_data['cursor_token'] != '':

            next_url += "/" + new_data['cursor_token']
            back_url += "/" + new_data['cursor_token']

        #prepare response

        serializer = UserBlocksSerializer(result['rows'], many=True)

        response = Response(
            data={
                'next_url': next_url,
                'back_url': back_url,
                'message': '',
                'data': serializer.data,
            },
            status=status.HTTP_200_OK
        )

        patch_cache_control(
            response,
            no_cache=True, no_store=True, must_revalidate=True, max_age=0
        )

        return response


    #perform blocking/unblocking
    def post(self, request, *args, **kwargs):

        serializer = CreateUserBlocksAPISerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data
        user_message = ""

        #get user to block
        blocked_user = get_object_or_404(get_user_model(), username_lowercase=new_data['username'].lower())

        #disallow users from blocking themselves
        if blocked_user.id == request.user.id:

            return Response(
                data={
                    'message': 'You cannot block yourself.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_data['to_block'] is True:

            #handle blocking
            UserBlocks.objects.get_or_create(
                user=request.user,
                blocked_user=blocked_user
            )

            user_message = "You have blocked " + blocked_user.username + "."

        else:

            #handle unblocking
            UserBlocks.objects.filter(
                user=request.user,
                blocked_user=blocked_user
            ).delete()

            user_message = "You have unblocked " + blocked_user.username + "."

        return Response(
            data={
                'message': user_message
            },
            status=status.HTTP_200_OK
        )



class UsersUsernameAPI(generics.GenericAPIView):

    serializer_class = UsersUsernameAPISerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    #checks if username exists
    @method_decorator(app_decorators.deny_if_banned("response"))
    def get(self, request, *args, **kwargs):

        serializer = UsersUsernameAPISerializer(data=kwargs, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        #proceed

        new_data = serializer.validated_data
        
        exists = get_user_model().objects.filter(
            username_lowercase=new_data['username'].lower()
        ).exists()

        return Response(
            {
                'data': {
                    'username': new_data['username'],
                    'exists': exists
                },
                'message': '',
            },
            status.HTTP_200_OK
        )


    #updates username, but only once, i.e. when username is None
    @method_decorator(app_decorators.deny_if_banned("response"))
    def post(self, request, *args, **kwargs):

        #user must not already have a username
        if request.user.username is not None:

            return Response(
                {
                    'message': 'You already have a username.',
                },
                status.HTTP_403_FORBIDDEN
            )

        #validate
        serializer = UsersUsernameAPISerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        #check again if it exists
        username_exists = get_user_model().objects.filter(
            username_lowercase=new_data['username'].lower()
        ).exists()

        if username_exists is True:

            return Response(
                data={
                    'data': {
                        'username': new_data['username'],
                        'exists': True
                    },
                    'message': 'Oops! That username is taken.'
                },
                status=status.HTTP_200_OK
            )
        
        #apply new username
        request.user.username = new_data['username']
        request.user.username_lowercase = new_data['username'].lower()
        request.user.save()

        return Response(
            data={
                'data': {
                    'username': new_data['username'],
                    'exists': False
                },
                'message': 'Your username is now %s!' % (new_data['username'])
            },
            status=status.HTTP_200_OK
        )



class UsersLogInSignUpAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = []
    current_context:Literal['log_in', 'sign_up'] = "log_in"


    def __init__(self, *args, **kwargs):

        if 'current_context' not in kwargs or kwargs['current_context'] not in ['log_in', 'sign_up']:

            raise custom_error(ValueError, dev_message="Incorrect current_context passed. Check .as_view() at urls.py.")
    
        super().__init__(*args, **kwargs)


    def verify_and_log_in(self, request, user_instance, handle_user_otp_class:HandleUserOTP, otp):

        #random delay to mitigate single-threaded brute force attack
        time.sleep(random.uniform(0.7, 3.5))

        #reminder that verify_otp() does all the checks for us
        if handle_user_otp_class.verify_otp(otp) is False:

            #wanted to not tell users when max attempts have been reached, to prevent email probing
            #but pros and cons conclude that without at least telling when to try again, UX will be frustrating
            verify_otp_timeout_s = handle_user_otp_class.get_otp_attempt_timeout_seconds_left()

            if verify_otp_timeout_s > 0:

                #timed out and wrong OTP
                message = "Timed out from too many %s attempts. Try again in " + get_pretty_datetime(verify_otp_timeout_s) + "."

                if self.current_context == 'log_in':
                    message = message % ("login")
                elif self.current_context == 'sign_up':
                    message = message % ("sign-up")

                return Response(
                    data={
                        'message': message,
                        'verify_otp_success': False
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            #not timed out but wrong OTP
            message = "Incorrect %s code."

            if self.current_context == 'log_in':
                message = message % ("login")
            elif self.current_context == 'sign_up':
                message = message % ("sign-up")

            return Response(
                data={
                    'message': message,
                    'verify_otp_success': False
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #OTP verified, continue

        #currently set to True because we have no implication for is_active=False
        #on is_active=False, login() will fail, as well as force_login() at tests
        user_instance.is_active = True

        #set last_login
        user_instance.last_login = get_datetime_now()

        #save
        user_instance.save()

        #log in
        login(request, user_instance)

        return Response(
            data={
                'message': 'You are now logged in!',
                'is_logged_in': True
            },
            status=status.HTTP_200_OK
        )


    #we let users log in even if banned
    @method_decorator([
        app_decorators.deny_if_already_logged_in("response"),
        csrf_protect
    ])
    def post(self, request, *args, **kwargs):

        serializer = UsersLogInSignUpAPISerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data
        user_instance = None

        #get user

        try:

            user_instance = get_user_model().objects.get(email_lowercase=new_data['email'].lower())

        except get_user_model().DoesNotExist:

            user_instance = get_user_model().objects.create_user(email=new_data['email'])

        #proceed with valid user_instance
        
        with transaction.atomic():

            #prepare
            handle_user_otp_class = HandleUserOTP(
                user_instance,
                settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
                settings.OTP_CREATION_TIMEOUT_S, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
                settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
            )
            handle_user_otp_class.guarantee_user_otp_instance()

            #handle request for new OTP
            if new_data['is_requesting_new_otp'] is True:

                new_otp = handle_user_otp_class.generate_otp()

                #only send email if has legitimate new OTP
                if len(new_otp) == settings.TOTP_NUMBER_OF_DIGITS:

                    template_title = ""
                    template_title_description = ""

                    if self.current_context == 'log_in':
                        template_title = "Code for login"
                        template_title_description = "Login code:"
                    elif self.current_context == 'sign_up':
                        template_title = "Code for sign-up"
                        template_title_description = "Sign-up code:"

                    handle_user_otp_class.send_otp_email(
                        new_data['email'],
                        template_title,
                        template_title_description,
                        new_otp
                    )

                    #email sent
                    message = "%s code has been sent to " + new_data['email'] + "."

                    if self.current_context == 'log_in':
                        message = message % ("Login")
                    elif self.current_context == 'sign_up':
                        message = message % ("Sign-up")

                    return Response(
                        data={
                            'message': message,
                        },
                        status=status.HTTP_200_OK
                    )

                else:

                    #could not generate OTP

                    otp_creation_timeout_s = handle_user_otp_class.get_otp_creation_timeout_seconds_left()

                    if otp_creation_timeout_s > 0:

                        #timed out from creating otp
                        message = "Timed out from too many codes sent. Try again in " + get_pretty_datetime(otp_creation_timeout_s) + "."

                        return Response(
                            data={
                                'message': message,
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    else:

                        #not supposed to reach here
                        raise custom_error(
                            IntegrityError,
                            dev_message="Could not generate OTP for user, but user is unexpectedly not timed out."
                        )

            #not requesting for OTP, continue

            return self.verify_and_log_in(request, user_instance, handle_user_otp_class, new_data['otp'])



class UsersLogOutAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = [IsAuthenticated]


    def post(self, request, *args, **kwargs):

        logout(request)

        return Response(
            data={
                'data': {
                    'is_logged_in': False
                },
                'message': 'You are now logged out!'
            },
            status=status.HTTP_200_OK
        )



class AudioClipTonesAPI(generics.GenericAPIView):

    serializer_class = AudioClipTonesSerializer
    permission_classes = []


    def get(self, request, *args, **kwargs):

        response = Response(
            data={
                'message': '',
                'data': AudioClipTonesSerializer(
                    AudioClipTones.objects.all(),
                    many=True
                ).data
            }
        )

        patch_cache_control(
            response,
            no_cache=False, no_store=False, must_revalidate=True, max_age=settings.AUDIO_CLIP_TONE_CACHE_AGE_S
        )

        return response



class GetEventsAPI(generics.GenericAPIView):

    serializer_class = EventsAndAudioClipsAPISerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


    def get_events_by_id(self, event_id):

        audio_clips = AudioClips.objects.prefetch_related(
            'audio_clip_role',
            'event',
            'event__generic_status',
            'event__eventreplyqueues',
            'audio_clip_tone',
            'generic_status',
            'user',
        ).raw(
            '''
            SELECT
                audio_clips.*,
                events.*,
                audio_clip_tones.*,
                generic_statuses.*,
                audio_clip_likes_dislikes.is_liked AS is_liked_by_user
            FROM audio_clips
            LEFT JOIN events ON audio_clips.event_id = events.id
            LEFT JOIN event_reply_queues ON events.id = event_reply_queues.event_id
            LEFT JOIN audio_clip_tones ON audio_clips.audio_clip_tone_id = audio_clip_tones.id
            LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id
                AND audio_clip_likes_dislikes.user_id = %s
            LEFT JOIN generic_statuses ON audio_clips.generic_status_id = generic_statuses.id
            WHERE audio_clips.event_id = %s
            AND audio_clips.is_banned IS FALSE
            AND generic_statuses.generic_status_name = %s
            ''',
            params=(
                self.request.user.id,
                event_id,
                'ok',
            )
        )

        return audio_clips


    def get(self, request, *args, **kwargs):

        #handle singular events view

        audio_clips = self.get_events_by_id(kwargs['event_id'])
        event_reply_queues = extract_event_reply_queues_once_per_event(audio_clips)

        events_and_audio_clips = []

        #since we get by event, we can lazily check one to see whether user is replying
        if len(audio_clips) > 0 and hasattr(audio_clips[0].event, 'eventreplyqueues') is True:

            events_and_audio_clips = LockedEventsAndAudioClipsAPISerializer(
                group_audio_clips_into_events_and_event_reply_queues(audio_clips, event_reply_queues),
                many=True
            ).data

        else:

            events_and_audio_clips = EventsAndAudioClipsAPISerializer(
                group_audio_clips_into_events(audio_clips),
                many=True
            ).data

        #user simply wants to check the post for an event
        response = Response(
            data={
                'data': events_and_audio_clips,
                'message': '',
            },
        )

        #previously, if user is replying, we don't cache the request
        #in regards to replying UI not disappearing when user revisits
        #we just disable cache all the time to ensure likes/dislikes consistency
        patch_cache_control(
            response,
            no_cache=True, no_store=True, must_revalidate=True, max_age=0
        )

        return response



class BrowseEventsAPI(generics.GenericAPIView):

    serializer_class = EventsAndAudioClipsAPISerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


    def get_latest_grouped_audio_clips(
        self,
        username:str='',
        timeframe:Literal['all', 'month', 'week', 'day']='all',
        audio_clip_role_name:Literal['originator', 'responder']='originator',
        audio_clip_tone_id:int=None,
        next_or_back:Literal['next', 'back']='next',
        cursor_token:str='',
    ):

        #we can reuse passed tokens as default on 0 rows fetched
        result = {
            'rows': [],
            'next_cursor_token': cursor_token,
            'back_cursor_token': cursor_token,
        }

        username_lowercase = username.lower()

        #handle cursor token

        decoded_cursor_token = {}
        cursor_params = []

        if cursor_token != '':

            try:

                #get audio_clips.when_created, audio_clips.id
                decoded_cursor_token = decode_cursor_token(cursor_token)

                cursor_params = [
                    decoded_cursor_token['when_created'],
                    decoded_cursor_token['id'], decoded_cursor_token['when_created'],
                ]

            except:

                raise custom_error(
                    ValueError,
                    user_message="Unable to fetch content due to faulty cursor token.",
                    dev_message="Token could not be decoded: " + cursor_token
                )

        #handle whether to display all audio_clip_tones, or specific

        audio_clip_tones_sql = {
            'join': '',
            'and': ''
        }
        audio_clip_tones_params = []

        if audio_clip_tone_id is None:

            if username_lowercase == '':

                audio_clip_tones_sql['join'] = '''
                    INNER JOIN audio_clip_tones ON audio_clips.audio_clip_tone_id = audio_clip_tones.id
                '''

                audio_clip_tones_sql['and'] = '''
                    AND audio_clip_tones.id IS NOT NULL
                '''

        else:

            audio_clip_tones_sql['join'] = '''
                INNER JOIN audio_clip_tones ON audio_clips.audio_clip_tone_id = audio_clip_tones.id
            '''
            audio_clip_tones_sql['and'] = '''
                AND audio_clip_tones.id = %s
            '''
            audio_clip_tones_params = [audio_clip_tone_id]

        #prepare timeframe
        #different checkpoints for different time range

        datetime_between = get_datetime_between(timeframe)

        #ran out of time to properly implement user blocks
        #i.e. prevent content from showing when blocking/blocked, either one-way or two-way
        #last checkpoint is getting excluded_event_ids the joining, but 1 blocked user with 100k events took 150+ms

        #prepare adjustments based on cursor direction

        cursor_sql = ''
        cursor_order_sql = ''

        if next_or_back == 'next':

            if len(decoded_cursor_token) > 0:

                cursor_sql = '''
                    AND (
                        audio_clips.when_created <= %s
                        AND
                        (audio_clips.id < %s OR audio_clips.when_created < %s)
                    )
                '''

            if username_lowercase != '':

                cursor_order_sql = '''ORDER BY audio_clips.is_banned DESC, audio_clips.when_created DESC, audio_clips.id DESC'''

            else:

                cursor_order_sql = '''ORDER BY audio_clips.when_created DESC, audio_clips.id DESC'''

        elif next_or_back == 'back':

            if len(decoded_cursor_token) > 0:

                cursor_sql = '''
                    AND (
                        audio_clips.when_created >= %s
                        AND
                        (audio_clips.id > %s OR audio_clips.when_created > %s)
                    )
                '''

            if username_lowercase != '':

                cursor_order_sql = '''ORDER BY audio_clips.is_banned DESC, audio_clips.when_created ASC, audio_clips.id ASC'''

            else:

                cursor_order_sql = '''ORDER BY audio_clips.when_created ASC, audio_clips.id ASC'''

        #main order, ensures cursor consistency
        #since our cursor goes from latest to earliest, our when_created and id must always be DESC here

        #it can be hard to guess where our priority rows end
        #e.g. incomplete or completed, or more than 1 originator/responder
        #so we sort our priority rows to "one half", then decide on cursor here in Py

        order_sql = '''
            ORDER BY
        '''
        order_params = []

        order_sql += '''
            CASE WHEN audio_clip_roles.audio_clip_role_name = %s
            THEN 1
            ELSE 2
            END,
        '''
        order_params.append(audio_clip_role_name)

        if username_lowercase != '':

            order_sql += '''
                CASE WHEN voicewake_user.username_lowercase = %s
                THEN 1
                ELSE 2
                END,
            '''
            order_params.append(username_lowercase)

        order_sql += '''
            audio_clips.when_created DESC, audio_clips.id DESC
        '''

        #adjust to being user-specific

        user_sql = {
            'target_audio_clips__join': '',
            'target_audio_clips__and': '',
            'join': '',
        }
        user_params = {
            'target_audio_clips__and': [],
        }

        if username_lowercase != '':

            user_sql['target_audio_clips__join'] = '''
                INNER JOIN voicewake_user ON audio_clips.user_id = voicewake_user.id
            '''
            user_sql['target_audio_clips__and'] = '''
                AND voicewake_user.username_lowercase = %s
            '''
            user_sql['join'] = '''
                INNER JOIN voicewake_user ON audio_clips.user_id = voicewake_user.id
            '''
            user_params['target_audio_clips__and'] = [username_lowercase]

        #handle event generic_status

        event_generic_status_name_sql = ''

        if username_lowercase != '':

            if audio_clip_role_name == 'originator':

                #for originator, show incomplete and completed for profile page
                event_generic_status_name_sql = '''
                    AND e_gs.generic_status_name IN ('incomplete', 'completed')
                '''

            elif audio_clip_role_name == 'responder':

                #show completed, but also deleted
                event_generic_status_name_sql = '''
                    AND e_gs.generic_status_name IN ('completed', 'deleted')
                '''

        else:

            event_generic_status_name_sql = '''
                AND e_gs.generic_status_name = 'completed'
            '''

        #handle extra info request.user is logged in
        #maybe this can be separately done to allow for caching in the future

        is_liked_by_user_sql = {
            'col': '',
            'join': ''
        }
        is_liked_by_user_params = []

        if self.request.user.is_authenticated is True:

            is_liked_by_user_sql['col'] = '''
                audio_clip_likes_dislikes.is_liked AS is_liked_by_user
            '''
            is_liked_by_user_sql['join'] = '''
                LEFT JOIN audio_clip_likes_dislikes
                    ON audio_clip_likes_dislikes.user_id = %s
                    AND audio_clips.id = audio_clip_likes_dislikes.audio_clip_id
            '''
            is_liked_by_user_params = [self.request.user.id]

        else:

            is_liked_by_user_sql['col'] = '''
                CAST(NULL AS bool) AS is_liked_by_user
            '''

        #get audio clips

        full_sql = '''
            WITH
            target_audio_clips AS (
                SELECT
                    audio_clips.event_id, audio_clips.when_created, audio_clips.id
                FROM audio_clips

                ''' + audio_clip_tones_sql['join'] + '''

                INNER JOIN audio_clip_roles ON audio_clips.audio_clip_role_id = audio_clip_roles.id
                INNER JOIN events ON audio_clips.event_id = events.id
                INNER JOIN generic_statuses AS ac_gs ON audio_clips.generic_status_id = ac_gs.id
                INNER JOIN generic_statuses AS e_gs ON events.generic_status_id = e_gs.id

                ''' + user_sql['target_audio_clips__join'] + '''

                WHERE audio_clips.is_banned IS FALSE

                ''' + audio_clip_tones_sql['and'] + '''

                AND ac_gs.generic_status_name = %s
                AND audio_clip_roles.audio_clip_role_name = %s

                ''' + event_generic_status_name_sql + '''
                ''' + user_sql['target_audio_clips__and'] + '''

                AND audio_clips.when_created BETWEEN %s AND %s

                ''' + cursor_sql + '''
                ''' + cursor_order_sql + '''

                LIMIT %s
            )
            SELECT audio_clips.*,

            ''' + is_liked_by_user_sql['col'] + '''

            FROM audio_clips
            RIGHT JOIN target_audio_clips ON audio_clips.event_id = target_audio_clips.event_id
            INNER JOIN generic_statuses AS ac_gs ON audio_clips.generic_status_id = ac_gs.id
            INNER JOIN audio_clip_roles ON audio_clips.audio_clip_role_id = audio_clip_roles.id

            ''' + user_sql['join'] + '''
            ''' + is_liked_by_user_sql['join'] + '''

            WHERE audio_clips.is_banned IS FALSE

            AND ac_gs.generic_status_name = %s
            ''' + order_sql + '''
        '''

        full_params = audio_clip_tones_params + [
            'ok',
            audio_clip_role_name,
        ] + user_params['target_audio_clips__and'] + [
            datetime_between['datetime_from'],
            datetime_between['datetime_to'],
        ] + cursor_params + [
            settings.EVENT_QUANTITY_PER_PAGE,
        ] + is_liked_by_user_params + [
            'ok',
        ] + order_params

        #execute

        audio_clips = AudioClips.objects.prefetch_related(
            'audio_clip_role',
            'event__generic_status',
            'event',
            'audio_clip_tone',
            'generic_status',
            'user',
        ).raw(
            full_sql,
            params=full_params
        )

        list(audio_clips)

        if len(audio_clips) == 0:

            return result
        
        result['rows'] = audio_clips

        #start preparing our cursor tokens
        #our desired audio_clip_role_name + username is always grouped to the first half

        result['back_cursor_token'] = encode_cursor_token({
            'when_created': audio_clips[0].when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
            'id': audio_clips[0].id,
        })

        last_relevant_index = 0

        for x in range(0, len(audio_clips)):

            if audio_clips[x].audio_clip_role.audio_clip_role_name == audio_clip_role_name:

                #edge case awareness
                #cursor is most accurate when at least 1 row with specified audio_clip_role_name is guaranteed to exist
                last_relevant_index = x

            else:

                break

        result['next_cursor_token'] = encode_cursor_token({
            'when_created': audio_clips[last_relevant_index].when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
            'id': audio_clips[last_relevant_index].id,
        })

        return result
    
        #overview
        #interesting caveats, unsure if it's due to flawed table structure or flawed query
            #user
                #when specified
                    #WITH ... ORDER BY must have extra unnecessary is_banned
                    #audio_clip_tone
                        #must leave out completely, cannot do IS NOT NULL
                        #other scenarios are fine, e.g.:
                            #no audio_clips with audio_clip_tone
                            #has audio_clips with audio_clip_tone but many
                #when not specified
                    #WITH ... ORDER BY does not need unnecessary is_banned
                    #audio_clip_tone
                        #can do IS NOT NULL
                        #other scenarios are fine, e.g.:
                            #no audio_clips with audio_clip_tone
                            #has audio_clips with audio_clip_tone but many

        #fixed: when user is specified, audio_clip_tones.id IS NOT NULL becomes around 250ms at 40k+ rows
            #remove join on audio_clip_tones when none specified

        #fixed: cursor goes through entire table, even with the correct index
            #for background, indexes work best when using/starting with "=" operator, or given a >= <= range
            #planner did not pick up on first "=" here:
                #AND (when_created = %s AND id < %s) OR (when_created < %s)
            #planner did pick up on first "=" here:
                #AND (when_created <= %s AND (id < %s OR when_created < %s))

        #fixed: cursor ORDER BY goes through entire table when no records are found for user
            #problem:
                #when no user selected, ok
                #when has user selected and guaranteed has rows, ok
                #when has user selected, many originator rows but 0 responder rows, query on responder scans entire table
            #solution:
                #index audio_clips on (when_created DESC, id DESC)
                    #index on id in composite index has no effect, but maybe it will when table gets much bigger
                #use dummy ORDER BY to discourage planner from using (when_created DESC) when no rows found
                    #settled with non-null is_banned DESC, while we always want False, so order is guaranteed

        #fixed:
            #problem:
                #selecting from audio_clips where specified audio_clip_tones.audio_clip_tone_slug does not match
                #causes entire audio_clips index scan
            #solution:
                #search by id, which handles fine when not exist, which also isn't confidential
                #compared to search by audio_clip_tone_slug, which we must do EXISTS() on every call otherwise
                #then when user doesn't want specific audio_clip_tones, change query to "IS NOT NULL"
            #extra context:
                #this issue persists when user is specified, but is also fixed using dummy ORDER BY is_banned


    #get event.id to simply view
    def get(self, request, *args, **kwargs):

        #validate, as a lot of our params accept only specific values
        serializer = BrowseEventsAPISerializer(data=kwargs, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        #get rows and cursor
        #currently only handling latest

        result = self.get_latest_grouped_audio_clips(
            username=new_data['username'],
            timeframe=new_data['timeframe'],
            audio_clip_role_name=new_data['audio_clip_role_name'],
            audio_clip_tone_id=new_data['audio_clip_tone_id'],
            next_or_back=new_data['next_or_back'],
            cursor_token=new_data['cursor_token'],
        )

        #prepare next and back URLs

        #get split url after removing next_or_back
        current_url_splits = self.request.build_absolute_uri().split(new_data['next_or_back'], 1)

        next_url = current_url_splits[0] + "next"
        back_url = current_url_splits[0] + "back"

        if len(result['rows']) > 0:

            #if we have > 0 rows, even with 1 row, both next and back cursor tokens will exist
            next_url = next_url + "/" + result['next_cursor_token']
            back_url = back_url + "/" + result['back_cursor_token']

        elif new_data['cursor_token'] != '':

            #reuse passed cursor token, if any
            next_url = next_url + "/" + new_data['cursor_token']
            back_url = back_url + "/" + new_data['cursor_token']

        #build the response

        response_data = group_audio_clips_into_events(result['rows'])
        response_data = EventsAndAudioClipsAPISerializer(response_data, many=True).data

        response = Response(
            data={
                'next_url': next_url,
                'back_url': back_url,
                'message': '',
                'data': response_data,
            },
            status=status.HTTP_200_OK
        )

        #we would preferrably cache the response
        #but because likes/dislikes are fetched together with it, caching interferes with likes/dislikes
        #we just disable cache all the time to ensure likes/dislikes consistency
        patch_cache_control(
            response,
            no_cache=True, no_store=True, must_revalidate=True, max_age=0
        )

        return response



#user can generate new event reply choice
    #will unlock previous is_replying=False event
    #will add to UserEvents when locking for is_replying=False
class ListEventReplyChoicesAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = [IsAuthenticated]

    #excludes event started by user
    #excludes event that user has talked in before, e.g. talked and banned, etc.
    #excludes those that blocked user, as well as those that the user has blocked, i.e. goes both ways
    def get_audio_clips_by_incomplete_events(self, audio_clip_tone_id:int=0):

        max_when_created = (get_datetime_now() - timedelta(seconds=settings.EVENT_INCOMPLETE_QUEUE_MAX_AGE_S))
        max_when_created = max_when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z')

        #do not get events where this user has been involved in before
        #we select only events.id in selected_events, followed by events JOIN
        #because if we do events.* in selected_events, we'll have to write all columns in GROUP BY clause

        audio_clip_tone_sql = ''
        audio_clip_tone_params = []

        if audio_clip_tone_id == 0:

            audio_clip_tone_sql = '''
                AND audio_clips.audio_clip_tone_id IS NOT NULL
            '''

        else:

            audio_clip_tone_sql = '''
                AND audio_clips.audio_clip_tone_id = %s
            '''
            audio_clip_tone_params.append(audio_clip_tone_id)

        full_sql = '''
            WITH
				excluded_events_1 AS (
                    SELECT event_id FROM audio_clips
                    WHERE user_id = %s
				),
				excluded_events_2 AS (
                    SELECT event_id FROM user_events
                    WHERE user_id = %s
                    AND when_excluded_for_reply IS NOT NULL
				),
                excluded_users_1 AS (
                    SELECT blocked_user_id AS id FROM user_blocks
                    WHERE user_id = %s
                ),
                excluded_users_2 AS (
                    SELECT user_id AS id FROM user_blocks
                    WHERE blocked_user_id = %s
                )
				SELECT audio_clips.*,
                audio_clip_likes_dislikes.is_liked AS is_liked_by_user
                FROM audio_clips
                INNER JOIN events ON audio_clips.event_id = events.id
				INNER JOIN audio_clip_roles ON audio_clips.audio_clip_role_id = audio_clip_roles.id
					AND audio_clip_roles.audio_clip_role_name = %s
				INNER JOIN generic_statuses AS ac_gs ON audio_clips.generic_status_id = ac_gs.id
					AND ac_gs.generic_status_name = %s
                INNER JOIN generic_statuses AS e_gs ON events.generic_status_id = e_gs.id
                    AND e_gs.generic_status_name = %s
				LEFT JOIN event_reply_queues ON audio_clips.event_id = event_reply_queues.event_id
				LEFT JOIN excluded_events_1 ON audio_clips.event_id = excluded_events_1.event_id
				LEFT JOIN excluded_events_2 ON audio_clips.event_id = excluded_events_2.event_id
				LEFT JOIN excluded_users_1 ON audio_clips.user_id = excluded_users_1.id
				LEFT JOIN excluded_users_2 ON audio_clips.user_id = excluded_users_2.id
                LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id
                    AND audio_clip_likes_dislikes.user_id = %s
				WHERE audio_clips.is_banned IS FALSE
				''' + audio_clip_tone_sql + '''
				AND event_reply_queues.id IS NULL
				AND excluded_events_1.event_id IS NULL
				AND excluded_events_2.event_id IS NULL
				AND excluded_users_1.id IS NULL
				AND excluded_users_2.id IS NULL
				AND events.when_created >= %s
				ORDER BY events.when_created ASC
				LIMIT %s
        '''

        full_params = [
            self.request.user.id,
            self.request.user.id,
            self.request.user.id,
            self.request.user.id,
            'originator',
            'ok',
            'incomplete',
            self.request.user.id,
        ] + audio_clip_tone_params + [
            max_when_created,
            settings.EVENT_INCOMPLETE_QUEUE_QUANTITY,
        ]

        #start
        audio_clips = AudioClips.objects.select_for_update(of=("self",)).prefetch_related(
            'audio_clip_role',
            'event__generic_status',
            'event',
            'audio_clip_tone',
            'generic_status',
            'user',
        ).raw(
            full_sql,
            full_params
        )

        return audio_clips


    def lock_events_for_reply_choices(self, audio_clips)->list[EventReplyQueues]:

        #this is to lock events to show to users as reply choices
        #not yet for replying

        event_ids = []
        bulk_events = []
        bulk_event_reply_queues = []
        datetime_now = get_datetime_now()

        for audio_clip in audio_clips:

            if audio_clip.event.id not in event_ids:

                bulk_event_reply_queues.append(
                    EventReplyQueues(
                        event=audio_clip.event,
                        when_locked = datetime_now,
                        locked_for_user = self.request.user,
                        is_replying = False,
                    )
                )
                event_ids.append(audio_clip.event.id)
                bulk_events.append(audio_clip.event)

        #store
        #at docs, bulk_create "returns created objects as a list, in the same order as provided"
        bulk_event_reply_queues = EventReplyQueues.objects.bulk_create(bulk_event_reply_queues)

        #prevent repeated queue
        #we do this here to encourage choosing the best audio_clip room, while leaving the other good ones for other users
        prevent_events_from_queuing_twice_for_reply(
            self.request.user,
            bulk_events
        )

        #Events and EventReplyQueues are 1-to-1
        #originators and Events are also 1-to-1
        if len(audio_clips) != len(bulk_event_reply_queues):

            raise custom_error(ValueError, 'Ratio of originators and EventReplyQueues is not 1-to-1 as expected.')

        return bulk_event_reply_queues


    #unlocks all
    def unlock_events_from_reply_choices(self):

        EventReplyQueues.objects.filter(
            locked_for_user=self.request.user
        ).delete()


    #only unlocks expired events
    def unlock_expired_events_from_reply_choices(self):

        datetime_now = get_datetime_now()

        #is_replying=False, a.k.a. reply choice
        EventReplyQueues.objects.filter(
            locked_for_user=self.request.user,
            is_replying=False,
            when_locked__lte=(datetime_now - timedelta(seconds=settings.EVENT_REPLY_CHOICE_MAX_DURATION_S))
        ).delete()

        #is_replying=True, a.k.a. replying
        EventReplyQueues.objects.filter(
            locked_for_user=self.request.user,
            is_replying=True,
            when_locked__lte=(datetime_now - timedelta(seconds=settings.EVENT_REPLY_MAX_DURATION_S))
        ).delete()


    #gets both is_replying=True/False events
    def get_audio_clips_from_locked_events(self)->list[AudioClips]:

        audio_clips = AudioClips.objects.prefetch_related(
            'audio_clip_role',
            'event__generic_status',
            'event',
            'audio_clip_tone',
            'generic_status',
            'user',
            Prefetch(
                'event__eventreplyqueues',
                queryset=EventReplyQueues.objects.filter(locked_for_user=self.request.user),
            ),
        ).raw(
            '''
            SELECT audio_clips.*,
                audio_clip_likes_dislikes.is_liked AS is_liked_by_user
            FROM audio_clips
            INNER JOIN generic_statuses ON audio_clips.generic_status_id = generic_statuses.id
			INNER JOIN event_reply_queues ON audio_clips.event_id = event_reply_queues.event_id
				AND event_reply_queues.locked_for_user_id = %s
            LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id
                AND audio_clip_likes_dislikes.user_id = %s
			WHERE audio_clips.is_banned IS FALSE
            AND generic_statuses.generic_status_name = %s
            ''',
            params=(
                self.request.user.id,
                self.request.user.id,
                'ok'
            )
        )

        return audio_clips


    #queue audio_clip room reply choices for user
    @method_decorator([
        app_decorators.deny_if_no_username("response"),
        app_decorators.deny_if_banned("response"),
    ])
    def post(self, request, *args, **kwargs):

        serializer = ListEventReplyChoicesAPISerializer(data=request.data, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        #check whether user wants to auto-skip current choices and get new ones

        if new_data['unlock_all_locked_events'] is True:

            #auto-remove all reply choices
            self.unlock_events_from_reply_choices()

        elif new_data['unlock_all_locked_events'] is False:

            #auto-remove expired reply choices only
            self.unlock_expired_events_from_reply_choices()

            #since user still wants non-expired reply choices, we get, if any
            audio_clips = self.get_audio_clips_from_locked_events()
            event_reply_queues = extract_event_reply_queues_once_per_event(audio_clips)

            if len(audio_clips) > 0:

                #return non-expired reply choices
                result = group_audio_clips_into_events_and_event_reply_queues(audio_clips, event_reply_queues)
                serializer = LockedEventsAndAudioClipsAPISerializer(result, many=True)

                return Response(
                    data={
                        'data': serializer.data,
                        'message': '',
                    },
                    status=status.HTTP_200_OK
                )

        #no existing reply choices, so check reply daily limit
        #borrow the check from CreateAudioClips

        create_audio_clips_class = CreateAudioClips(
            self.request.user, "create_reply",
            settings.EVENT_CREATE_DAILY_LIMIT, settings.EVENT_REPLY_DAILY_LIMIT,
            settings.EVENT_REPLY_MAX_DURATION_S,
        )

        cooldown_s = create_audio_clips_class.get_cooldown_on_audio_clip_create_limit_s()

        if cooldown_s > 0:

            return Response(
                data={
                    'message': "Come back in " + get_pretty_datetime(cooldown_s) + "!",
                    'event_reply_daily_limit_reached': True,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #proceed with getting new reply choices

        try:

            with transaction.atomic():

                audio_clips = self.get_audio_clips_by_incomplete_events(audio_clip_tone_id=new_data['audio_clip_tone_id'])

                if len(audio_clips) == 0:

                    #no eligible events
                    return Response(
                        data={
                            'data': [],
                            'message': '',
                        },
                        status=status.HTTP_200_OK
                    )

                #lock events and get event_reply_queues
                event_reply_queues = self.lock_events_for_reply_choices(audio_clips)

                #return
                result = group_audio_clips_into_events_and_event_reply_queues(audio_clips, event_reply_queues)
                serializer = LockedEventsAndAudioClipsAPISerializer(result, many=True)

                return Response(
                    data={
                        'data': serializer.data,
                        'message': '',
                    },
                    status=status.HTTP_200_OK
                )

        except Exception as e:

            traceback.print_exc()

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )



#purposely not check UserBlocks here
#else a few unnecessary edge cases must be dealt with, since blocking someone is spammable
class HandleReplyingEventsAPI(generics.GenericAPIView):

    serializer_class = HandleReplyingEventsAPISerializer
    permission_classes = [IsAuthenticated]
    current_context:Literal['start', 'reply', 'cancel'] = "start"


    def __init__(self, *args, **kwargs):

        if 'current_context' not in kwargs or kwargs['current_context'] not in ['start', 'reply', 'cancel']:

            raise custom_error(ValueError, dev_message="Incorrect current_context. Check .as_view() at urls.py.")
    
        super().__init__(*args, **kwargs)


    def check_user_is_replying_in_other_events(self, excluded_event_id:int=None)->bool:

        if excluded_event_id is not None:

            #check if user is replying to anything, besides excluded event_id
            the_count = EventReplyQueues.objects.filter(
                locked_for_user=self.request.user,
                is_replying=True
            ).exclude(
                pk=excluded_event_id
            ).count()

        else:

            #check if user is replying to anything at all
            the_count = EventReplyQueues.objects.filter(
                locked_for_user=self.request.user,
                is_replying=True
            ).count()

        return the_count > 0


    def unlock_reply_choices(self, excluded_event_id:int=None):

        if excluded_event_id is not None:

            EventReplyQueues.objects.filter(
                locked_for_user=self.request.user
            ).exclude(
                pk=excluded_event_id
            ).delete()

        else:

            EventReplyQueues.objects.filter(
                locked_for_user=self.request.user
            ).delete()


    #if user is already locked for event, change (is_replying=False) to (is_replying=True, when_locked!=None)
    #no need to check for daily reply limit here
    def start_reply_in_event(self, event_id:int):

        #check if user is replying to any other event
        if self.check_user_is_replying_in_other_events(excluded_event_id=event_id) is True:

            return Response(
                data={
                    'message': 'You are already replying in a different event.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        #not yet replying to anything, proceed

        datetime_now = get_datetime_now()

        target_event_reply_queue = EventReplyQueues.objects.select_for_update(
            of=("self",)
        ).select_related(
            'event__generic_status',
        ).get(
            locked_for_user=self.request.user,
            event_id=event_id,
        )

        #deny if already replying
        if target_event_reply_queue.is_replying is True:

            return Response(
                data={
                    'message': 'You are already replying in this event.',
                },
                status=status.HTTP_200_OK
            )

        #not yet replying, proceed

        #check and ensure event availability
        if target_event_reply_queue.event.generic_status.generic_status_name != 'incomplete':

            #remove expired reply choice
            target_event_reply_queue.delete()

            return Response(
                data={
                    'message': 'This event is no longer available for reply.',
                    'can_retry': False,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #check for expiry
        if(
            target_event_reply_queue.when_locked <
            (datetime_now - timedelta(seconds=settings.EVENT_REPLY_CHOICE_MAX_DURATION_S))
        ):

            #remove expired reply choice
            target_event_reply_queue.delete()

            return Response(
                data={
                    'message': 'The choice to reply in this event has expired.',
                    'can_retry': False,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #not yet expired, proceed

        #unlock other reply choices
        self.unlock_reply_choices(excluded_event_id=target_event_reply_queue.event_id)

        #user is officially replying
        target_event_reply_queue.when_locked = datetime_now
        target_event_reply_queue.is_replying = True
        target_event_reply_queue.save()

        serializer = EventReplyQueuesSerializer(
            [target_event_reply_queue],
            many=True
        )

        return Response(
            data={
                'data': serializer.data,
                'message': 'You are now replying in this event.',
            },
            status=status.HTTP_200_OK
        )


    def create_reply_in_event(self, event_id:int, audio_clip_tone_id:int, audio_file):

        create_audio_clips_class = CreateAudioClips(
            self.request.user, "create_reply",
            settings.EVENT_CREATE_DAILY_LIMIT, settings.EVENT_REPLY_DAILY_LIMIT,
            settings.EVENT_REPLY_MAX_DURATION_S,
        )

        return create_audio_clips_class.create_audio_clip_as_responder(
            event_id, audio_clip_tone_id, audio_file
        )


    #as long as EventReplyQueue for correct locked_for_user and event_id exists, delete
    #no need to check for further details
    def cancel_reply_in_event(self, event_id:int):

        #directly delete, i.e. no get() necessary
        deleted_count, deleted_rows = EventReplyQueues.objects.filter(
            locked_for_user=self.request.user,
            event_id=event_id
        ).delete()

        if deleted_count == 0:

            raise EventReplyQueues.DoesNotExist

        #intentionally have no message
        #UI does not need it
        return Response(
            data={
                'message': '',
            },
            status=status.HTTP_200_OK
        )


    #start/cancel reply after reply choice has already been locked for the user
    @method_decorator([
        app_decorators.deny_if_no_username("response"),
        app_decorators.deny_if_banned("response"),
    ])
    def post(self, request, *args, **kwargs):

        serializer = None

        if self.current_context == 'start' or self.current_context == 'cancel':

            serializer = HandleReplyingEventsAPISerializer(data=request.data, many=False)

        elif self.current_context == 'reply':

            serializer = CreateAudioClipsAPISerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        #check for required args that are considered as optional in serializer
        if 'event_id' not in new_data:

            return Response(
                data={
                    'message': "Missing 'event_id'.",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #proceed

        try:

            with transaction.atomic():

                if self.current_context == "start":

                    #start replying
                    return self.start_reply_in_event(new_data['event_id'])

                elif self.current_context == "reply":

                    #reply
                    return self.create_reply_in_event(
                        new_data['event_id'],
                        new_data['audio_clip_tone_id'],
                        new_data['audio_file'],
                    )

                elif self.current_context == "cancel":

                    #delete event_reply_queue
                    return self.cancel_reply_in_event(new_data['event_id'])

        except AudioClipTones.DoesNotExist:

            return Response(
                data={
                    'message': 'Your selected tag was not found. Try a different one.',
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Events.DoesNotExist:

            return Response(
                data={
                    'message': 'This event no longer exists.',
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        except EventReplyQueues.DoesNotExist:

            return Response(
                data={
                    'message': 'That action is no longer allowed for this event.',
                    'can_retry': False,
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except TimeoutError as e:

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except ValueError as e:

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except subprocess.CalledProcessError as e:

            return Response(
                data={
                    'message': 'Make sure your recording is not completely silent.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:

            traceback.print_exc()

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )



#does not have own get(), since viewing audio_clips always involves parent events
#handle creating audio_clips
    #if audio_clip_role_name='originator', create event
    #if audio_clip_role_name='responder', link to event and reset lock
class CreateEventsAPI(generics.GenericAPIView):

    serializer_class = CreateAudioClipsAPISerializer
    permission_classes = [IsAuthenticated]
    queryset = None


    @method_decorator([
        app_decorators.deny_if_no_username("response"),
        app_decorators.deny_if_banned("response"),
    ])
    def post(self, request, *args, **kwargs):

        #deserialize
        serializer = CreateAudioClipsAPISerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        #check for required args that are considered as optional in serializer
        if 'event_name' not in new_data:

            return Response(
                data={
                    'message': "Missing 'event_name'.",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #ok, proceed

        try:

            with transaction.atomic():

                create_audio_clips_class = CreateAudioClips(
                    self.request.user, "create_event",
                    settings.EVENT_CREATE_DAILY_LIMIT, settings.EVENT_REPLY_DAILY_LIMIT,
                    settings.EVENT_REPLY_MAX_DURATION_S,
                )

                return create_audio_clips_class.create_event_and_audio_clip_as_originator(
                    new_data["event_name"],
                    new_data["audio_clip_tone_id"],
                    new_data["audio_file"],
                )

        except AudioClipTones.DoesNotExist:

            return Response(
                data={
                    'message': 'Your selected tag was not found. Try a different one.',
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        except TimeoutError as e:

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except ValueError as e:

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except subprocess.CalledProcessError as e:

            return Response(
                data={
                    'message': 'Make sure your recording is not completely silent.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:

            traceback.print_exc()

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )



#to submit likes/dislikes
#is_liked=True/False, or destroy when undone
class AudioClipLikesDislikesAPI(generics.GenericAPIView):

    serializer_class = AudioClipLikesDislikesSerializer
    permission_classes = [IsAuthenticated]

    #no get() needed, since likes/dislikes are tied directly to audio_clips

    #create
    @method_decorator([
        app_decorators.deny_if_no_username("response"),
        app_decorators.deny_if_banned("response"),
    ])
    def post(self, request, *args, **kwargs):

        serializer = CreateAudioClipLikesDislikesSerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        #initially had checks on whether audio_clip exists, and whether it is already banned
        #instead, we now let db catch the error for us, because these checks are unnecessary in 99% of all cases

        #start

        try:

            if new_data['is_liked'] is None:

                #this is safe from "performing deletion but no rows found"
                AudioClipLikesDislikes.objects.filter(
                    user_id=request.user.id,
                    audio_clip_id=new_data['audio_clip_id']
                ).delete()

            else:

                #for value changes, use defaults arg
                AudioClipLikesDislikes.objects.update_or_create(
                    user_id=request.user.id,
                    audio_clip_id=new_data['audio_clip_id'],
                    defaults={'is_liked': new_data['is_liked']}
                )

        except IntegrityError as e:

            if type(e.__context__) == UniqueViolation:

                #this is no big deal
                #catches FK duplicates and when FK doesn't exist
                pass

            else:

                traceback.print_exc()

                return Response(
                    data={
                        'message': 'Unable to like and dislike this recording.',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except:

            traceback.print_exc()

            return Response(
                data={
                    'message': 'Unable to like and dislike this recording.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            data={
                'message': '',
            },
            status=status.HTTP_200_OK
        )

        #these solutions didn't help prevent race condition
            #direct .filter().update(like_count=F('like_count') + 1)
            #like_count = F('like_count) + 1; .save()
        #what worked:
            #using trigger that also checks for OLD.is_liked != NEW.is_liked during INSERT prevents race condition
        #peculiar:
            #with/without trigger, both at Locust had yielded the same response times (avg. 17000ms)































