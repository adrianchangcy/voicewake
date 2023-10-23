from django.http import JsonResponse, QueryDict
from django.db.models import Case, Value, When, Sum, Q, F, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.utils.cache import patch_cache_control
from django.utils.decorators import method_decorator

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


    def get(self, request, *args, **kwargs):






        return Response(
            data={
                'data': {
                
                },
                'message': ''
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

            #return any first error message
            error_message = "Invalid data."

            for key in serializer.errors:
                for first_error in serializer.errors[key]:
                    error_message = first_error
                    break

            return Response(
                data={
                    'message': error_message,
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_data = serializer.validated_data

        try:

            #get audio_clip
            target_audio_clip = AudioClips.objects.get(pk=new_data['reported_audio_clip_id'])

        except AudioClips.DoesNotExist:

            return Response(
                data={
                    'message': 'Recording does not exist.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #check if audio_clip belongs to user
        if target_audio_clip.user.id == request.user.id:

            return Response(
                data={
                    'message': 'You cannot report your own recording.',
                },
                status=status.HTTP_200_OK
            )

        #check if already banned
        if target_audio_clip.is_banned is True:

            return Response(
                data={
                    'message': 'This recording has already been banned.',
                },
                status=status.HTTP_200_OK
            )

        #add report
        AudioClipReports.objects.get_or_create(
            user_id=request.user.id,
            reported_audio_clip_id=new_data['reported_audio_clip_id']
        )

        return Response(
            data={
                'message': 'We will evaluate the report soon. Thank you for helping to make this a better place.',
            },
            status=status.HTTP_200_OK
        )



class UserBannedAudioClipsAPI(generics.GenericAPIView):

    serializer_class = AudioClipsSerializer
    permission_classes = [IsAuthenticated]

    #no post() here, once an audio_clip is banned, nobody can do anything
    #cronjob does the banning

    #user wants to see their own banned audio_clips
    def get(self, request, *args, **kwargs):

        if 'page' not in kwargs:

            return Response(
                data={
                    'message': 'No page specified in URL.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        offset_quantity = settings.BAN_AUDIO_CLIP_QUANTITY_PER_PAGE * (kwargs['page'] - 1)

        qs = AudioClips.objects.select_related(
            'user', 'audio_clip_tone'
        ).filter(
            user=request.user
        ).order_by('-when_created')[
            offset_quantity : offset_quantity + settings.BAN_AUDIO_CLIP_QUANTITY_PER_PAGE
        ]

        banned_audio_clips = []

        if len(qs) > 0:

            banned_audio_clips = AudioClipsSerializer(
                qs,
                many=True
            ).data

        response = Response(
            data={
                'data': banned_audio_clips,
                'message': ''
            },
            status=status.HTTP_200_OK
        )

        patch_cache_control(
            response,
            no_cache=True, no_store=True, must_revalidate=True, max_age=0
        )

        return response



class UserBlocksAPI(generics.GenericAPIView):

    serializer_class = UserBlocksSerializer
    permission_classes = [IsAuthenticated]


    #get list of blocked users
    def get(self, request, *args, **kwargs):

        if 'page' not in kwargs:

            return Response(
                data={
                    'message': 'No page specified in URL.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        offset_quantity = settings.GENERAL_ROW_QUANTITY_PER_PAGE * (kwargs['page'] - 1)

        qs = UserBlocks.objects.select_related(
            'blocked_user'
        ).filter(
            user=request.user
        ).order_by('blocked_user__username')[
            offset_quantity : offset_quantity + settings.GENERAL_ROW_QUANTITY_PER_PAGE
        ]

        serializer = UserBlocksSerializer(
            qs,
            many=True
        )

        response = Response(
            data={
                'data': serializer.data,
                'message': ''
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

        serializer = UserBlocksAPISerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            #return any first error message
            error_message = "Invalid data."

            for key in serializer.errors:
                for first_error in serializer.errors[key]:
                    error_message = first_error
                    break

            return Response(
                data={
                    'message': error_message,
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

            #return any first error message
            error_message = "Invalid data."

            for key in serializer.errors:
                for first_error in serializer.errors[key]:
                    error_message = first_error
                    break

            return Response(
                data={
                    'message': error_message,
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
                'message': 'Request successful.',
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

            #return any first error message
            error_message = "Invalid data."

            for key in serializer.errors:
                for first_error in serializer.errors[key]:
                    error_message = first_error
                    break

            return Response(
                data={
                    'message': error_message,
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
    current_context = ""


    def __init__(self, *args, **kwargs):

        if 'current_context' not in kwargs or kwargs['current_context'] not in ['log_in', 'sign_up']:

            raise custom_error(ValueError, dev_message="Incorrect current_context passed. Check .as_view() at urls.py.")
    
        super().__init__(*args, **kwargs)


    def verify_and_log_in(self, request, user_instance, handle_user_otp_class:HandleUserOTP, otp):

        #reminder that verify_otp() does all the checks for us
        if handle_user_otp_class.verify_otp(otp) is False:

            #do not let users know about max attempts reached
            #this protects against email probing during login
            return get_default_verify_otp_response()

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

            #return any first error message
            error_message = "Invalid data."

            for key in serializer.errors:
                for first_error in serializer.errors[key]:
                    error_message = first_error
                    break

            return Response(
                data={
                    'message': error_message,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data
        user_instance = None

        #get user
        #reminder that user shall always exist if following through account creation
        try:

            user_instance = get_user_model().objects.get(email_lowercase=new_data['email'].lower())

        except get_user_model().DoesNotExist:

            if self.current_context == "log_in":

                #we do this to obscure clues that a user may or may not exist
                if new_data['is_requesting_new_otp'] is True:
                
                    #no need to notify non-registered emails on login attempts
                    #prevents the attack where our website is used as the source of DDOS (towards Gmail in this case)
    
                    #fake delay
                    #during testing, send_mail() takes quite long, around 2+ secs
                    time.sleep(random.uniform(0.7, 3.5))
    
                    return get_default_create_otp_response(email=new_data['email'])
                
                else:

                    return get_default_verify_otp_response()
                
            elif self.current_context == "sign_up":

                user_instance = get_user_model().objects.create_user(email=new_data['email'])

        #proceed with valid user_instance
        
        with transaction.atomic():

            #prepare
            handle_user_otp_class = HandleUserOTP(
                user_instance,
                settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_SECONDS, settings.TOTP_TOLERANCE_SECONDS,
                settings.OTP_CREATE_TIMEOUT_SECONDS, settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
            )
            handle_user_otp_class.get_or_create_user_otp_instance()

            #handle request for new OTP
            if new_data['is_requesting_new_otp'] is True:

                new_otp = handle_user_otp_class.generate_otp()

                #only send email if has legitimate new OTP
                if len(new_otp) == settings.TOTP_NUMBER_OF_DIGITS:

                    template_title = ""
                    template_title_description = ""

                    if self.current_context == 'log_in':
                        template_title = "Code for login"
                        template_title_description = "Log in with this code:"
                    elif self.current_context == 'sign_up':
                        template_title = "Code for sign-up"
                        template_title_description = "Sign up with this code:"

                    handle_user_otp_class.send_otp_email(
                        new_data['email'],
                        template_title,
                        template_title_description,
                        new_otp
                    )

                else:

                    #fake delay
                    time.sleep(random.uniform(0.7, 3.5))

                return get_default_create_otp_response(new_data['email'])

            #continue to verifying OTP and logging in
            #will always return Response()
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
            no_cache=False, no_store=False, must_revalidate=True, max_age=settings.AUDIO_CLIP_TONE_CACHE_AGE_SECONDS
        )

        return response



class EventsAPI(generics.GenericAPIView):

    serializer_class = GroupedAudioClipsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


    def get_events_by_completed(
        self, latest_or_best:Literal['latest', 'best']='latest',
        audio_clip_tone_slug:str='',
        timeframe:Literal['day', 'week', 'month', 'all']='all',
        page=1
    ):

        #when audio_clip_tone_slug is '', will just get entire audio_clip_tones
        #when timeframe is 'all_time', leaving datetime_from as '' is sufficient
        #since this is non-user page, i.e. front page, show "latest" events once only
        #page starts from 1

        if page < 1:

            raise ValueError("'page' parameter must be >= 1.")

        #different checkpoints for different time range
        datetime_checkpoint_timedelta = {
            'day': timedelta(days=1),
            'week': timedelta(days=7),
            'month': timedelta(days=31)
        }

        #calculate time range
        #leave datetime_from as '' if you want "of all time"
        datetime_from = ''
        datetime_to = get_datetime_now(True)

        #determine earliest possible datetime
        if timeframe in datetime_checkpoint_timedelta:

            datetime_from = (get_datetime_now() - datetime_checkpoint_timedelta[timeframe]).strftime('%Y-%m-%d %H:%M:%S %z')

        else:

            #getting earliest audio_clips.when_created adds 5-10ms
            #using custom function get_id_of_events_by_when_created() adds 40ms+

            #random datetime that is guaranteed beyond earliest audio_clips row is the best so far
            #here are the risks where this may/would break things:
                #new audio_clips.when_created can start using past datetime
                #audio_clips.when_created is no longer secured by auto_now_add
                #suddenly no longer uses time zone
            datetime_from = '2020-01-01 01:01:01 +00'

        #calculate offset for pagination
        pagination_offset = (page - 1) * settings.EVENT_QUANTITY_PER_PAGE

        #prevent showing twice
        previously_shown_events_sql = {'join': '', 'and': ''}

        if latest_or_best == 'latest':

            previously_shown_events_sql['join'] = 'LEFT JOIN previously_shown_event_ids ON audio_clips.event_id = previously_shown_event_ids.id'
            previously_shown_events_sql['and'] = 'AND previously_shown_event_ids.id IS NULL'

        #determine order
        order_sql = ''

        if latest_or_best == 'best':
            order_sql = 'ORDER BY audio_clips.like_count DESC, audio_clips.dislike_count ASC'
        else:
            order_sql = 'ORDER BY audio_clips.when_created DESC'

        #some notes on compromise
            #desired
                #userA blocks userB, userA won't see userB content, vice versa
                #however, if userB is in same event as userA, then show
            #issue
                #desired situation requires another excluded_users, and "audio_clips.user_id=userA OR ..."
                #the OR condition brings query time from 10ms+ to 40ms+
            #current
                #userA blocks userB, userA won't see any content from userB at all

        #start
        #we get by completed events, i.e. guaranteed ok audio_clips
        #then, since banned audio_clips are still associated with events, get only ok audio_clips
        audio_clips = AudioClips.objects.prefetch_related(
            'audio_clip_role',
            'event__generic_status',
            'event__created_by',
            'event',
            'audio_clip_tone',
            'generic_status',
            'user',
        ).raw(
            '''		
            WITH
                selected_audio_clip_tones AS (
                    SELECT id FROM get_id_of_one_or_all_audio_clip_tones_via_slug(%s)
                ),
                previously_shown_event_ids AS (
                    SELECT event_id AS id FROM user_events
                    WHERE user_id = %s
                    AND when_seen_at_front_page IS NOT NULL
                ),
                excluded_users AS (
                    SELECT blocked_user_id AS id FROM user_blocks
                    WHERE user_id = %s
                ),
                excluded_event_ids AS (
                    SELECT event_id AS id FROM audio_clips
                    RIGHT JOIN excluded_users ON audio_clips.user_id = excluded_users.id
                ),
                selected_event_ids AS (
                    SELECT DISTINCT event_id AS id FROM (
                        SELECT audio_clips.event_id FROM audio_clips
                        RIGHT JOIN selected_audio_clip_tones ON audio_clips.audio_clip_tone_id = selected_audio_clip_tones.id
                        LEFT JOIN excluded_event_ids ON audio_clips.event_id = excluded_event_ids.id
                        ''' + previously_shown_events_sql['join'] + '''
                        LEFT JOIN audio_clip_tones ON audio_clips.audio_clip_tone_id = audio_clip_tones.id
                        LEFT JOIN events ON audio_clips.event_id = events.id
                        LEFT JOIN generic_statuses AS events_generic_statuses ON events.generic_status_id = events_generic_statuses.id
                        WHERE events_generic_statuses.generic_status_name = %s
                        AND excluded_event_ids.id IS NULL
                        ''' + previously_shown_events_sql['and'] + '''
                        AND audio_clips.when_created BETWEEN %s AND %s
                        ''' + order_sql + '''
                    )
                    AS distinct_event_ids
                    OFFSET %s LIMIT %s
                )
            SELECT
                audio_clips.*,
                events.*,
                audio_clip_tones.*,
                generic_statuses.*,
                audio_clip_likes_dislikes.is_liked AS is_liked_by_user
            FROM audio_clips
            RIGHT JOIN selected_event_ids ON audio_clips.event_id = selected_event_ids.id
            LEFT JOIN events ON audio_clips.event_id = events.id
            LEFT JOIN audio_clip_tones ON audio_clips.audio_clip_tone_id = audio_clip_tones.id
            LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id AND audio_clip_likes_dislikes.user_id = %s
            LEFT JOIN generic_statuses ON audio_clips.generic_status_id = generic_statuses.id
            WHERE audio_clips.is_banned IS FALSE
            AND generic_statuses.generic_status_name = %s
            ''',
            params=(
                audio_clip_tone_slug,
                self.request.user.id,
                self.request.user.id,
                'completed',
                datetime_from,
                datetime_to,
                pagination_offset,
                settings.EVENT_QUANTITY_PER_PAGE,
                self.request.user.id,
                'ok'
            )
        )

        return audio_clips


    def get_events_by_user_and_audio_clip_role(
        self, username:str, audio_clip_role_name:str,
        latest_or_best:Literal['latest', 'best']='latest',
        audio_clip_tone_slug:str='',
        timeframe:Literal['day', 'week', 'month', 'all']='all',
        page=1
    ):

        #when audio_clip_tone_slug is '', will just get entire audio_clip_tones
        #when timeframe is 'all_time', leaving datetime_from as '' is sufficient
        #page starts from 1

        if page < 1 or len(username) == 0 or len(audio_clip_role_name) == 0:

            raise ValueError("One or more required parameters are missing.")

        #different checkpoints for different time range
        datetime_checkpoint_timedelta = {
            'day': timedelta(days=1),
            'week': timedelta(days=7),
            'month': timedelta(days=31)
        }

        #calculate time range
        #leave datetime_from as '' if you want "of all time"
        datetime_from = ''
        datetime_to = get_datetime_now(True)

        #determine earliest possible datetime
        if timeframe in datetime_checkpoint_timedelta:

            datetime_from = (get_datetime_now() - datetime_checkpoint_timedelta[timeframe]).strftime('%Y-%m-%d %H:%M:%S %z')

        else:

            #getting earliest audio_clips.when_created adds 5-10ms
            #using custom function get_id_of_events_by_when_created() adds 40ms+

            #random datetime that is guaranteed beyond earliest audio_clips row is the best so far
            #here are the risks where this may/would break things:
                #new audio_clips.when_created can start using past datetime
                #audio_clips.when_created is no longer secured by auto_now_add
                #suddenly no longer uses time zone
            datetime_from = '2020-01-01 01:01:01 +00'

        #calculate offset for pagination
        pagination_offset = (page - 1) * settings.EVENT_QUANTITY_PER_PAGE

        #determine order
        order_sql = ''

        if latest_or_best == 'best':
            order_sql = 'ORDER BY audio_clips.like_count DESC, audio_clips.dislike_count ASC'
        else:
            order_sql = 'ORDER BY audio_clips.when_created DESC'

        #start
        #get events from role-specific audio_clips where audio_clips are ok, i.e. as long as one audio_clip is ok
        #then, we get only ok audio_clips
        audio_clips = AudioClips.objects.prefetch_related(
            'audio_clip_role',
            'event__generic_status',
            'event__created_by',
            'event',
            'audio_clip_tone',
            'generic_status',
            'user',
        ).raw(
            '''		
            WITH
                selected_audio_clip_tones AS (
                    SELECT id FROM get_id_of_one_or_all_audio_clip_tones_via_slug(%s)
                ),
                selected_event_ids AS (
                    SELECT DISTINCT event_id AS id FROM (
                        SELECT audio_clips.event_id FROM audio_clips
                        RIGHT JOIN selected_audio_clip_tones ON audio_clips.audio_clip_tone_id = selected_audio_clip_tones.id
                        LEFT JOIN voicewake_user ON audio_clips.user_id = voicewake_user.id
                        LEFT JOIN audio_clip_tones ON audio_clips.audio_clip_tone_id = audio_clip_tones.id
                        LEFT JOIN events ON audio_clips.event_id = events.id
                        LEFT JOIN audio_clip_roles ON audio_clips.audio_clip_role_id = audio_clip_roles.id
                        LEFT JOIN generic_statuses ON audio_clips.generic_status_id = generic_statuses.id
                        WHERE voicewake_user.username_lowercase = %s
                        AND audio_clips.is_banned IS FALSE
                        AND generic_statuses.generic_status_name = %s
                        AND audio_clip_roles.audio_clip_role_name = %s
                        AND audio_clips.when_created BETWEEN %s AND %s
                        ''' + order_sql + '''
                    )
                    AS distinct_event_ids
                    OFFSET %s LIMIT %s
                )
            SELECT
                audio_clips.*,
                events.*,
                audio_clip_tones.*,
                generic_statuses.*,
                audio_clip_likes_dislikes.is_liked AS is_liked_by_user
            FROM audio_clips
            RIGHT JOIN selected_event_ids ON audio_clips.event_id = selected_event_ids.id
            LEFT JOIN events ON audio_clips.event_id = events.id
            LEFT JOIN audio_clip_tones ON audio_clips.audio_clip_tone_id = audio_clip_tones.id
            LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id AND audio_clip_likes_dislikes.user_id = %s
            LEFT JOIN generic_statuses ON audio_clips.generic_status_id = generic_statuses.id
            WHERE audio_clips.is_banned IS FALSE
            AND generic_statuses.generic_status_name = %s
            ''',
            params=(
                audio_clip_tone_slug,
                username.lower(),
                'ok',
                audio_clip_role_name,
                datetime_from,
                datetime_to,
                pagination_offset,
                settings.EVENT_QUANTITY_PER_PAGE,
                self.request.user.id,
                'ok',
            )
        )

        return audio_clips


    def get_events_by_id(self, event_id):

        audio_clips = AudioClips.objects.prefetch_related(
            'audio_clip_role',
            'event__generic_status',
            'event__created_by',
            'event',
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
            LEFT JOIN audio_clip_tones ON audio_clips.audio_clip_tone_id = audio_clip_tones.id
            LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id AND audio_clip_likes_dislikes.user_id = %s
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


    #get event.id to simply view
    def get(self, request, *args, **kwargs):

        #handle singular events view
        if 'event_id' in kwargs:

            #user simply wants to check the post for an event
            response = Response(
                data={
                    'message': '',
                    'data': GroupedAudioClipsSerializer(
                        group_audio_clips_into_events(self.get_events_by_id(self.kwargs['event_id'])),
                        many=True
                    ).data,
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
        
        #proceed to handling multiple events
        
        #pagination
        url_page = 1
        if 'page' in kwargs and kwargs['page'] > 1:
            #URL page starts from 1
            #>1 above allows us to ensure 0 is not used
            url_page = kwargs['page']

        #audio_clip_tone
        #leave empty to get all
        url_audio_clip_tone_slug = ''
        if 'audio_clip_tone_slug' in kwargs:
            url_audio_clip_tone_slug = kwargs['audio_clip_tone_slug']

        #determine the appropriate results
        response = None

        if(
            'username' in kwargs and 'latest_or_best' in kwargs and
            'timeframe' in kwargs and 'audio_clip_role_name' in kwargs
        ):

            response = Response(
                data={
                    'message': '',
                    'data': GroupedAudioClipsSerializer(
                        group_audio_clips_into_events(
                            self.get_events_by_user_and_audio_clip_role(
                                kwargs['username'],
                                kwargs['audio_clip_role_name'],
                                kwargs['latest_or_best'],
                                url_audio_clip_tone_slug,
                                kwargs['timeframe'],
                                url_page,
                            )
                        ),
                        many=True
                    ).data,
                },
                status=status.HTTP_200_OK
            )
        
        elif 'latest_or_best' in kwargs and 'timeframe' in kwargs and 'page':

            grouped_events = group_audio_clips_into_events(
                self.get_events_by_completed(
                    kwargs['latest_or_best'],
                    url_audio_clip_tone_slug,
                    kwargs['timeframe'],
                    url_page,
                )
            )

            #for non-user page, i.e. front page, only show once for latest
            if request.user.is_authenticated is True and kwargs['latest_or_best'] == 'latest':

                events = []

                for row in grouped_events:

                    events.append(row['event'])

                prevent_events_from_showing_twice_at_front_page(request.user, events)

            response = Response(
                data={
                    'message': '',
                    'data': GroupedAudioClipsSerializer(
                        grouped_events,
                        many=True
                    ).data,
                },
                status=status.HTTP_200_OK
            )

        #ok
        if response is not None:

            #we would preferrably cache the response
            #but because likes/dislikes are fetched together with it, caching interferes with likes/dislikes
            #we just disable cache all the time to ensure likes/dislikes consistency
            patch_cache_control(
                response,
                no_cache=True, no_store=True, must_revalidate=True, max_age=0
            )

            return response

        #invalid URL
        return Response(
            data={
                'message': 'Invalid URL.',
                'data': []
            },
            status=status.HTTP_400_BAD_REQUEST
        )



#user can generate new event reply choice
    #will unlock previous is_replying=False event
    #will add to UserEvents when locking for is_replying=False
class HandleEventReplyChoicesAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = [IsAuthenticated]
    current_context = ""


    def __init__(self, *args, **kwargs):

        if 'current_context' not in kwargs or kwargs['current_context'] not in ['list', 'expire']:

            raise custom_error(ValueError, dev_message="Incorrect current_context passed. Check .as_view() at urls.py.")

        super().__init__(*args, **kwargs)


    def lock_events_for_reply_choices(self, audio_clips):

        event_ids = []
        events = []
        datetime_now = get_datetime_now()

        for audio_clip in audio_clips:

            if audio_clip.event.id not in event_ids:

                event_ids.append(audio_clip.event.id)

                #lock for reply choices
                audio_clip.event.when_locked = datetime_now
                audio_clip.event.locked_for_user = self.request.user
                audio_clip.event.is_replying = False
                audio_clip.event.last_modified = datetime_now

                events.append(audio_clip.event)

        Events.objects.bulk_update(events, ['when_locked', 'locked_for_user', 'is_replying', 'last_modified'])

        #prevent repeated queue
        #we do this here to encourage choosing the best audio_clip room, while leaving the other good ones for other users
        prevent_events_from_queuing_twice_for_reply(
            self.request.user,
            events
        )

        return True


    #excludes event started by user
    #excludes event that user has talked in before, e.g. talked and banned, etc.
    #excludes those that blocked user, as well as those that the user has blocked, i.e. goes both ways
    def get_events_by_random_incomplete(self, audio_clip_tone_slug:str=''):

        datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))
        datetime_now = datetime_now.strftime('%Y-%m-%d %H:%M:%S %z')

        #start
        #do not get events where this user has been involved in before
        #we select only events.id in selected_events, followed by events JOIN
        #because if we do events.* in selected_events, we'll have to write all columns in GROUP BY clause
        audio_clips = AudioClips.objects.select_for_update(of=("event",)).prefetch_related(
            'audio_clip_role',
            'event__generic_status',
            'event__created_by',
            'event',
            'audio_clip_tone',
            'generic_status',
            'user',
        ).raw(
            '''
            WITH
                selected_audio_clip_tones AS (
                    SELECT id FROM get_id_of_one_or_all_audio_clip_tones_via_slug(%s)
                ),
                past_involved_events_1 AS (
                    SELECT event_id FROM audio_clips
                    WHERE user_id = %s
                ),
                past_involved_events_2 AS (
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
                ),
                selected_events AS (
                    SELECT events.id AS id FROM events
                    INNER JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
                    LEFT JOIN past_involved_events_1 ON events.id = past_involved_events_1.event_id
                    LEFT JOIN past_involved_events_2 ON events.id = past_involved_events_2.event_id
                    LEFT JOIN excluded_users_1 ON events.created_by_id = excluded_users_1.id
                    LEFT JOIN excluded_users_2 ON events.created_by_id = excluded_users_2.id
                    WHERE generic_statuses.generic_status_name = %s
                    AND past_involved_events_1.event_id IS NULL
                    AND past_involved_events_2.event_id IS NULL
                    AND excluded_users_1.id IS NULL
                    AND excluded_users_2.id IS NULL
                    AND locked_for_user_id IS NULL
                    AND created_by_id != %s
                    ORDER BY events.when_created DESC
                    LIMIT %s
                )
            SELECT
                audio_clips.*,
                selected_events.*,
                audio_clip_tones.*,
                generic_statuses.*,
                audio_clip_likes_dislikes.is_liked AS is_liked_by_user
            FROM audio_clips
            RIGHT JOIN selected_events ON audio_clips.event_id = selected_events.id
            RIGHT JOIN selected_audio_clip_tones ON audio_clips.audio_clip_tone_id = selected_audio_clip_tones.id
            LEFT JOIN audio_clip_roles ON audio_clips.audio_clip_role_id = audio_clip_roles.id
            LEFT JOIN events ON selected_events.id = events.id
            LEFT JOIN audio_clip_tones ON audio_clips.audio_clip_tone_id = audio_clip_tones.id
            LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id AND audio_clip_likes_dislikes.user_id = %s
            LEFT JOIN generic_statuses ON audio_clips.generic_status_id = generic_statuses.id
            WHERE generic_statuses.generic_status_name = %s
            AND audio_clips.is_banned IS FALSE
            AND audio_clip_roles.audio_clip_role_name = %s
            ''',
            params=(
                audio_clip_tone_slug,
                self.request.user.id,
                self.request.user.id,
                self.request.user.id,
                self.request.user.id,
                'incomplete',
                self.request.user.id,
                settings.EVENT_INCOMPLETE_ROLL_QUANTITY,
                self.request.user.id,
                'ok',
                'originator'
            )
        )

        return audio_clips


    def unlock_events_from_past_reply_choices(self):

        User = get_user_model()
        datetime_now = get_datetime_now()

        events = Events.objects.select_for_update().filter(
            locked_for_user=self.request.user
        )
        
        for event in events:

            #unlock
            event.when_locked = None
            event.locked_for_user = None
            event.is_replying = None
            event.last_modified = datetime_now

        Events.objects.bulk_update(events, ['when_locked', 'locked_for_user', 'is_replying', 'last_modified'])


    def get_events_by_is_replying(self):

        audio_clips = AudioClips.objects.prefetch_related(
            'audio_clip_role',
            'event__generic_status',
            'event__created_by',
            'event',
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
            LEFT JOIN audio_clip_tones ON audio_clips.audio_clip_tone_id = audio_clip_tones.id
            LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id AND audio_clip_likes_dislikes.user_id = %s
            LEFT JOIN generic_statuses ON audio_clips.generic_status_id = generic_statuses.id
            LEFT JOIN generic_statuses AS events_generic_statuses ON events.generic_status_id = events_generic_statuses.id
            WHERE events.locked_for_user_id = %s
            AND events_generic_statuses.generic_status_name = %s
            AND events.is_replying = %s
            AND audio_clips.is_banned IS FALSE
            AND generic_statuses.generic_status_name = %s
            ''',
            params=(
                self.request.user.id,
                self.request.user.id,
                'incomplete',
                True,
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

        if self.current_context == "list":

            #get possible is_replying
            is_replying_audio_clips = self.get_events_by_is_replying()

            #check if user is replying to anything
            #we want event.id if there is any
            if len(is_replying_audio_clips) > 0:

                return Response(
                    data={
                        'message': '',
                        'data': GroupedAudioClipsSerializer(
                            group_audio_clips_into_events(is_replying_audio_clips),
                            many=True
                        ).data,
                    },
                )
            
        #check if user has specified audio_clip_tones
        serializer = HandleEventReplyChoicesAPISerializer(data=request.data, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': 'Invalid data.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_data = serializer.validated_data

        specified_audio_clip_tone = None

        try:

            if 'audio_clip_tone_id' in new_data:

                specified_audio_clip_tone = AudioClipTones.objects.get(pk=new_data['audio_clip_tone_id'])

        except AudioClipTones.DoesNotExist:

            return Response(
                data={
                    'message': 'Specified audio_clip_tone_id does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:

            with transaction.atomic():

                #user is not replying, continue
                if self.current_context == "list":

                    #not replying, can unlock previous choices if any
                    self.unlock_events_from_past_reply_choices()

                    #maybe don't unlock on every search
                    #only unlock on skip

                    #get audio_clips
                    audio_clips = None

                    if specified_audio_clip_tone is None:
                        audio_clips = self.get_events_by_random_incomplete()
                    else:
                        audio_clips = self.get_events_by_random_incomplete(audio_clip_tone_slug=specified_audio_clip_tone.audio_clip_tone_slug)

                    if len(audio_clips) == 0:

                        return Response(
                            data={
                                'message': '',
                                'data': GroupedAudioClipsSerializer(
                                    [],
                                    many=True
                                ).data,
                            },
                            status=status.HTTP_200_OK
                        )

                    #lock audio_clips
                    self.lock_events_for_reply_choices(audio_clips)

                    #return audio_clips sorted by events
                    return Response(
                        data={
                            'message': '',
                            'data': GroupedAudioClipsSerializer(
                                group_audio_clips_into_events(audio_clips),
                                many=True
                            ).data,
                        },
                        status=status.HTTP_200_OK
                    )
        
                elif self.current_context == "expire":

                    #has expired, so unlock
                    self.unlock_events_from_past_reply_choices()

                    return Response(
                        data={
                            'message': 'The audio_clip choice has expired. Feel free to search again!'
                        },
                        status=status.HTTP_205_RESET_CONTENT
                    )

                else:

                    raise custom_error(
                        AttributeError,
                        dev_message="Invalid user_context arg from urls.py."
                    )
                
        except Exception as e:

            traceback.print_exc()

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )



class HandleReplyingEventsAPI(generics.GenericAPIView):

    serializer_class = HandleReplyingEventsAPISerializer
    permission_classes = [IsAuthenticated]
    current_context = ""


    def __init__(self, *args, **kwargs):

        if 'current_context' not in kwargs or kwargs['current_context'] not in ['start', 'delete']:

            raise custom_error(ValueError, dev_message="Incorrect current_context. Check .as_view() at urls.py.")
    
        super().__init__(*args, **kwargs)


    #if user is already locked for event, do is_replying=True and update when_locked
    #for actual replying to start
    #202 success, 205 reset due to user inactivity
    def start_replying_to_event(self, event_id):

        User = get_user_model()
        datetime_now = get_datetime_now()

        #check if user is replying to any other event
        if check_user_is_replying(request=self.request, excluded_event_id=event_id) is True:

            return Response(
                data={
                    'message': 'You are already replying in a different audio_clip.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            with transaction.atomic():

                #get event
                #we want to do select_for_update(), but it's not allowed for nullable joins, so we do exclude()
                #also, you must add coma (,) to of=("self",), else it gets unpacked into "s","e","l","f"
                target_event = Events.objects.select_related(
                    'generic_status', 'locked_for_user'
                ).select_for_update(
                    of=("self",)
                ).exclude(
                    locked_for_user=None
                ).get(
                    pk=event_id
                )

                user = User(self.request.user.id)

                #check if target_event is already locked for user beforehand
                #check if target_event is not yet expired as a choice
                #check if target_event is locked for the correct user
                #if you want to do "extend when_locked", handle target_event.is_replying=True
                if\
                    target_event.generic_status.generic_status_name == 'incomplete' and\
                    target_event.when_locked is not None and\
                    (get_datetime_now() - target_event.when_locked).total_seconds() <= settings.EVENT_REPLY_CHOICE_EXPIRY_SECONDS and\
                    target_event.locked_for_user is not None and target_event.locked_for_user.id == self.request.user.id and\
                    target_event.is_replying is False\
                :

                    pass

                else:

                    if settings.DEBUG is True:

                        print(target_event.generic_status.generic_status_name == 'incomplete')
                        print(target_event.when_locked is not None)
                        print((datetime_now - target_event.when_locked).total_seconds() <= settings.EVENT_REPLY_CHOICE_EXPIRY_SECONDS)
                        print(target_event.locked_for_user is not None and target_event.locked_for_user.id == self.request.user.id)
                        print(target_event.is_replying)

                    raise custom_error(
                        ValueError,
                        user_message="You cannot start replying to this audio_clip."
                    )

                #can reply, proceed

                #unlock any other audio_clip rooms that were locked for reply choices
                #also save to user_events to prevent unlocked events from being queued twice
                events = Events.objects.filter(
                    locked_for_user=user
                ).select_for_update(
                    of=("self",)
                ).exclude(
                    pk=event_id
                )

                for event in events:

                    event.when_locked = None
                    event.locked_for_user = None
                    event.is_replying = None
                    event.last_modified = datetime_now

                #unlock
                Events.objects.bulk_update(events, ['when_locked', 'locked_for_user', 'is_replying', 'last_modified'])

                #confirm reply, start over when_locked
                target_event.when_locked = get_datetime_now()
                target_event.is_replying = True
                target_event.save()

                return Response(
                    data={
                        'message': 'Success! You are now replying to this audio_clip.',
                    },
                    status=status.HTTP_202_ACCEPTED
                )
            
        except Events.DoesNotExist:

            return Response(
                data={
                    'message': 'This audio_clip either no longer exists, or is unavailable.',
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:

            traceback.print_exc()

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )


    #if user has already selected a reply choice and is now replying, allow to cancel
    #401 not allowed to cancel or has already cancelled
    def delete_replying_to_event(self, event_id):

        try:

            with transaction.atomic():

                #get event
                event = Events.objects.select_related(
                    'generic_status', 'locked_for_user'
                ).select_for_update(
                    of=("self",)
                ).get(
                    pk=event_id
                )

                #check if user is already replying
                #we don't check for time limit, as cancellation can occur beyond it
                if\
                    event.when_locked is not None and\
                    event.is_replying is True and\
                    event.locked_for_user is not None and event.locked_for_user.id == self.request.user.id\
                :

                    pass

                else:

                    #under these conditions, we want to allow cancellation without error
                    #UI being removed is of higher priority than status_code
                    return Response(
                        data={
                            'message': 'You are not replying to this audio_clip.',
                        },
                        status=status.HTTP_401_UNAUTHORIZED
                    )

                #cancel replying
                event.locked_for_user = None
                event.is_replying = None
                event.when_locked = None

                event.save()

                return Response(
                    data={
                        'message': 'Reply has been deleted.',
                    },
                    status=status.HTTP_200_OK
                )
            
        except Events.DoesNotExist:

            return Response(
                data={
                    'message': 'This audio_clip either no longer exists, or is unavailable.',
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )


    #start/cancel reply after reply choice has already been locked for the user
    @method_decorator([
        app_decorators.deny_if_no_username("response"),
        app_decorators.deny_if_banned("response"),
    ])
    def post(self, request, *args, **kwargs):

        serializer = HandleReplyingEventsAPISerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            #return any first error message
            error_message = "Invalid data."

            for key in serializer.errors:
                for first_error in serializer.errors[key]:
                    error_message = first_error
                    break

            return Response(
                data={
                    'message': error_message,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        #proceed

        if self.current_context == "start":

            return self.start_replying_to_event(new_data['event_id'])
        
        elif self.current_context == "delete":

            return self.delete_replying_to_event(new_data['event_id'])



#does not have own get(), since viewing audio_clips always involves parent events
#handle creating audio_clips
    #if audio_clip_role_name='originator', create event
    #if audio_clip_role_name='responder', link to event and reset lock
class AudioClipsAPI(generics.GenericAPIView):

    serializer_class = CreateAudioClipsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = None
    current_context = ""


    def __init__(self, *args, **kwargs):

        if 'current_context' not in kwargs or kwargs['current_context'] not in ['create_new', 'reply']:

            raise custom_error(ValueError, dev_message="Incorrect current_context passed. Check .as_view() at urls.py.")
    
        super().__init__(*args, **kwargs)


    def check_user_create_event_daily_limit(self, user):

        #this is for "X max new audio_clip rooms every __", which in this case is every 24h
        datetime_checkpoint = datetime.now().astimezone(tz=ZoneInfo('UTC')).strftime('%Y-%m-%d 00:00:00 %z')
        datetime_checkpoint = datetime.strptime(datetime_checkpoint, '%Y-%m-%d %H:%M:%S %z')

        the_count = Events.objects.filter(
            created_by=user,
            when_created__gte=datetime_checkpoint
        ).count()

        if the_count < settings.EVENT_CREATE_DAILY_LIMIT:

            return False

        return True


    def check_user_create_reply_audio_clip_daily_limit(self, user):

        #this is for "X max new posts every __", which in this case is every 24h
        datetime_checkpoint = datetime.now().astimezone(tz=ZoneInfo('UTC')).strftime('%Y-%m-%d 00:00:00 %z')
        datetime_checkpoint = datetime.strptime(datetime_checkpoint, '%Y-%m-%d %H:%M:%S %z')

        the_count = AudioClips.objects.filter(
            user=user,
            when_created__gte=datetime_checkpoint
        ).count()

        if the_count < settings.EVENT_REPLY_DAILY_LIMIT:

            return False

        return True


    def check_user_can_reply_event(self, event):

        #check if user is replying
        if\
            event.locked_for_user is not None and\
            event.locked_for_user.id == self.request.user.id and\
            event.is_replying is True\
        :

            return True

        return False


    def check_user_exceeded_reply_time_window(self, event):

        minutes_passed = (get_datetime_now() - event.when_locked).total_seconds()

        if minutes_passed > settings.EVENT_REPLY_CHOICE_EXPIRY_SECONDS:

            return True
        
        return False


    @method_decorator([
        app_decorators.deny_if_no_username("response"),
        app_decorators.deny_if_banned("response"),
    ])
    def post(self, request, *args, **kwargs):

        #deserialize
        serializer = CreateAudioClipsSerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            #return any first error message
            error_message = "Invalid data."

            for key in serializer.errors:
                for first_error in serializer.errors[key]:
                    error_message = first_error
                    break

            return Response(
                data={
                    'message': error_message,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #ok, continue
        new_data = serializer.validated_data

        try:

            with transaction.atomic():

                #audio_clip_tone
                audio_clip_tone = AudioClipTones.objects.get(pk=new_data['audio_clip_tone_id'])

                #determine if originator/responder, then create/get event
                #generic_status is handled by default, so it is skipped here
                if self.current_context == "create_new":

                    #check if created event limit is not yet reached
                    if self.check_user_create_event_daily_limit(request.user) is True:

                        raise custom_error(
                            TimeoutError,
                            user_message="You have reached your daily limit for creating audio_clips."
                        )

                    #proceed
                    audio_clip_role = AudioClipRoles.objects.get(audio_clip_role_name='originator')

                    event = Events.objects.create(
                        event_name=new_data['event_name'],
                        generic_status=GenericStatuses.objects.get(generic_status_name='incomplete'),
                        created_by=request.user
                    )

                elif self.current_context == "reply":

                    #check if reply audio_clip limit is not yet reached
                    if self.check_user_create_reply_audio_clip_daily_limit(request.user) is True:

                        raise custom_error(
                            ValueError,
                            user_message="You have reached your daily limit of replies."
                        )

                    #get event
                    event = Events.objects.select_for_update().get(pk=new_data['event_id'])

                    #check if this user is already attached beforehand
                    if self.check_user_can_reply_event(event) is False:

                        raise custom_error(
                            ValueError,
                            user_message="This audio_clip is no longer available for reply."
                        )
                    
                    #check if user exceeded reply time window but automated script has not detected yet
                    if self.check_user_exceeded_reply_time_window(event) is True:

                        #reset
                        event.locked_for_user = None
                        event.when_locked = None
                        event.is_replying = None
                        event.save()

                        raise custom_error(
                            TimeoutError,
                            user_message="Reply was not successful. You had reached the time limit."
                        )

                    #mark event as completed, remove lock
                    event.generic_status = GenericStatuses.objects.get(generic_status_name='completed')
                    event.when_locked = None
                    event.locked_for_user = None
                    event.is_replying = None
                    event.save()

                    #can proceed
                    audio_clip_role = AudioClipRoles.objects.get(audio_clip_role_name='responder')
                
                #proceed

                #audio_file, further validation
                #on error, will raise by themselves
                handle_audio_file_class = HandleAudioFile(new_data['audio_file'], True)

                #prepare audio file info, which also self-validates
                #reminder that .size check should be done at form/serializer
                handle_audio_file_class.prepare_audio_file_info()

                #normalize
                handle_audio_file_class.do_normalisation()

                #get peaks
                handle_audio_file_class.get_peaks_by_buckets()

                #create audio_clip, excluding audio_file and event
                #generic_status is handled by default, so it is skipped here
                new_audio_clip = AudioClips.objects.create(
                    user=request.user,
                    audio_clip_role=audio_clip_role,
                    audio_clip_tone=audio_clip_tone,
                    event=event,
                    audio_volume_peaks=handle_audio_file_class.peak_buckets,
                    audio_duration_s=handle_audio_file_class.audio_file_duration_s
                )

                #we delay saving audio_file, as we want when_created for audio_file's path
                new_audio_clip.audio_file = handle_audio_file_class.audio_file
                new_audio_clip.save()

                #close just in case it's no longer a reference, i.e. Django won't auto-close
                handle_audio_file_class.close_audio_file()

                return Response(
                    {
                        'data': {
                            'event_id': event.id
                        },
                        'message': 'Success!',
                    },
                    status.HTTP_201_CREATED
                )
        
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
                    'message': 'This audio_clip no longer exists.',
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

            print(get_dev_message_from_custom_error(e))

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

            #return any first error message
            error_message = "Invalid data."

            for key in serializer.errors:
                for first_error in serializer.errors[key]:
                    error_message = first_error
                    break

            return Response(
                data={
                    'message': error_message,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        try:

            target_audio_clip = AudioClips.objects.get(pk=new_data['audio_clip_id'])

            #check if audio_clip is banned
            if target_audio_clip.is_banned is True:

                return Response(
                    data={
                        'message': 'This recording has been banned.',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except AudioClips.DoesNotExist:

            return Response(
                data={
                    'message': 'This recording no longer exists.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #these solutions didn't help prevent race condition
            #direct .filter().update(like_count=F('like_count') + 1)
            #like_count = F('like_count) + 1; .save()
        #what worked:
            #using trigger that also checks for OLD.is_liked != NEW.is_liked during INSERT prevents race condition
        #peculiar:
            #with/without trigger, both at Locust had yielded the same response times (avg. 17000ms)

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

                #this is no big deal, as unique constraint has just done its job of protecting us from duplicates
                pass

            else:

                traceback.print_exc()

                return Response(
                    data={
                        'message': 'Unable to like/dislike this audio_clip.',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except:

            traceback.print_exc()

            return Response(
                data={
                    'message': 'Unable to like/dislike this audio_clip.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            data={
                'message': '',
            },
            status=status.HTTP_200_OK
        )




























