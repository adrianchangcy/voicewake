from django.http import JsonResponse, QueryDict
from django.db.models import Case, Value, When, Sum, Q, F, Count, BooleanField
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.utils.cache import patch_cache_control
from django.utils.decorators import method_decorator
from django.db.models import Prefetch
from django.db.utils import IntegrityError
from django.urls import reverse
from django.core.cache import cache
from redis.exceptions import ConnectionError

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
from voicewake.tasks import *
import voicewake.decorators as app_decorators
from django.conf import settings

#specifically just for error handling
from psycopg.errors import UniqueViolation
from django.db.utils import IntegrityError



#all APIs should stay consistent to this response format:
    #return Response(
    #    data={
    #        'message': '',
    #        'data': [CustomSerializer(instance=db_rows, many=True).data],
    #        'arbitrary_value': 1,
    #    },
    #    status=status.HTTP_400_BAD_REQUEST
    #)



#extra ideas for features
#increased creative competition
    #have limited events for this category
    #24 hours to create + reply, another 24 hours to vote
    #fun acknowledgement on voting correctly



class TestAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = []
    url_context = ""


    def get(self, request, *args, **kwargs):


        return Response(
            data={
                'data': {
                },
                'message': '',
            },
            status=status.HTTP_200_OK
        )











class UsersLogInSignUpAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = []
    available_contexts = ['log_in', 'sign_up']
    url_context:Literal['log_in', 'sign_up'] = 'log_in'


    def __init__(self, *args, **kwargs):

        if 'url_context' not in kwargs or kwargs['url_context'] not in self.available_contexts:

            raise custom_error(
                ValueError,
                __name__,
                dev_message="Incorrect url_context passed. Check .as_view() at urls.py."
            )
    
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

                if self.url_context == 'log_in':
                    message = message % ("login")
                elif self.url_context == 'sign_up':
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

            if self.url_context == 'log_in':
                message = message % ("login")
            elif self.url_context == 'sign_up':
                message = message % ("sign-up")

            return Response(
                data={
                    'message': message,
                    'verify_otp_success': False
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #OTP verified, continue

        #finally do is_active=True
        #so we can regularly clean up is_active=False accounts who failed to fully register, e.g. email impersonation
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

        request_data = serializer.validated_data
        user_instance = None

        #get user

        try:

            user_instance = get_user_model().objects.get(email_lowercase=request_data['email'].lower())

        except get_user_model().DoesNotExist:

            user_instance = get_user_model().objects.create_user(email=request_data['email'])

        #proceed with valid user_instance

        with transaction.atomic():

            #prepare
            handle_user_otp_class = HandleUserOTP(
                user_instance,
                settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_S, settings.TOTP_TOLERANCE_S,
                settings.OTP_CREATION_TIMEOUT_S, settings.OTP_MAX_CREATIONS, settings.OTP_MAX_CREATIONS_TIMEOUT_S,
                settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPTS_TIMEOUT_S
            )

            handle_user_otp_class.guarantee_user_otp_instance(select_for_update=True)

            #handle request for new OTP
            if request_data['is_requesting_new_otp'] is True:

                new_otp = handle_user_otp_class.generate_otp()

                #only send email if has legitimate new OTP
                if len(new_otp) == settings.TOTP_NUMBER_OF_DIGITS:

                    #add task to Celery
                    task_send_otp_email.s(
                        context=self.url_context,
                        email=request_data['email'],
                        otp=new_otp,
                    ).delay()

                    #email sent
                    message = "%s code has been sent to " + request_data['email'] + "."

                    if self.url_context == 'log_in':
                        message = message % ("Login")
                    elif self.url_context == 'sign_up':
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

                        return Response(
                            data={
                                'error_code': 'otp-creation-timeout',
                                'timeout_s': otp_creation_timeout_s,
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    else:

                        #not supposed to reach here
                        raise custom_error(
                            IntegrityError,
                            __name__,
                            dev_message="Could not generate OTP for user, but user is unexpectedly not timed out."
                        )

            #not requesting for OTP, continue

            return self.verify_and_log_in(request, user_instance, handle_user_otp_class, request_data['otp'])



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

        request_data = serializer.validated_data
        
        exists = get_user_model().objects.filter(
            username_lowercase=request_data['username'].lower()
        ).exists()

        return Response(
            {
                'data': {
                    'username': request_data['username'],
                    'exists': exists
                },
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

        request_data = serializer.validated_data

        #check again if it exists
        username_exists = get_user_model().objects.filter(
            username_lowercase=request_data['username'].lower()
        ).exists()

        if username_exists is True:

            return Response(
                data={
                    'data': {
                        'username': request_data['username'],
                        'exists': True
                    },
                    'message': 'Oops! That username is taken.'
                },
                status=status.HTTP_200_OK
            )
        
        #apply new username
        request.user.username = request_data['username']
        request.user.username_lowercase = request_data['username'].lower()
        request.user.save()

        return Response(
            data={
                'data': {
                    'username': request_data['username'],
                    'exists': False
                },
                'message': 'Your username is now %s!' % (request_data['username'])
            },
            status=status.HTTP_200_OK
        )



class UserBlocksAPI(generics.GenericAPIView):

    serializer_class = UserBlocksSerializer
    permission_classes = [IsAuthenticated]


    def determine_when_last_action_s_cache_key(self, user_id:int):

        return 'user_blocks_when_last_action_s_' + str(user_id)


    #can only get user's own block list
    def get(self, request, *args, **kwargs):

        #ensure cache exists

        when_last_action_s = cache.get(self.determine_when_last_action_s_cache_key(self.request.user.id), None)

        if when_last_action_s is None:

            latest_row = None

            try:

                latest_row = UserBlocks.objects.filter(user=self.request.user).latest('when_created')

                #proceeds to fetching all rows

            except UserBlocks.DoesNotExist:

                #early detection of 0 rows in db
                #ensure cache exists so subsequent requests with no new actions won't query db again

                when_last_action_s = math.trunc(get_datetime_now().timestamp())

                cache.set(
                    self.determine_when_last_action_s_cache_key(self.request.user.id),
                    when_last_action_s
                )

                #already know 0 rows in db, so return
                return Response(
                    data={
                        'data': [],
                        'when_last_action_s': when_last_action_s,
                    },
                    status=status.HTTP_200_OK
                )

            when_last_action_s = math.trunc(latest_row.when_created.timestamp())

            cache.set(
                self.determine_when_last_action_s_cache_key(self.request.user.id),
                when_last_action_s
            )

        #check if frontend wants to check for sync
        #do comparison via math.trunc() value of datetime.timestamp(), i.e. seconds since UNIX epoch, a.k.a. posix

        passed_when_last_action_s = self.request.GET.get('when_last_action_s', None)

        if passed_when_last_action_s is not None:

            #validate

            try:

                passed_when_last_action_s = int(passed_when_last_action_s)

            except:

                return Response(
                    data={
                        'message': "Invalid when_last_action_s passed.",
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            

            #check if frontend is in sync with cache

            if passed_when_last_action_s == when_last_action_s:

                #frontend and cache are up-to-date

                return Response(
                    data={
                        'data': [],
                        'is_up_to_date': True,
                    },
                    status=status.HTTP_200_OK
                )

        #not in sync, or frontend does not care
        #continue with fetching rows

        #for something as simple as only requiring 1 column, serializing and returning as {} for every row is overkill
        #test results at 1000 rows via Content-Length header: serializer (66900 bytes), list (18900 bytes)
        #also confirmed via self.assertNumQueries(1) at test for queryset below

        result = UserBlocks.objects.select_related('blocked_user').filter(user=request.user).order_by('when_created').values_list('blocked_user__username')

        usernames = []

        #transform tuple-per-object into list

        for row in result:

            usernames.append(row[0])

        response = Response(
            data={
                'data': usernames,
                'when_last_action_s': when_last_action_s
            },
            status=status.HTTP_200_OK
        )

        patch_cache_control(
            response,
            no_cache=True, no_store=True, must_revalidate=True, max_age=0
        )

        return response


    #perform blocking/unblocking
    @method_decorator(app_decorators.deny_if_banned("response"))
    def post(self, request, *args, **kwargs):

        #wanted to allow for bulk changes via usernames=[...], but it is overkill for what this feature is
        #initially also returned when_last_action_s
            #but it can give frontend a false confirmation of sync if frontend performs POST with outdated store
            #therefore, POST no longer returns when_last_action_s

        serializer = PostUserBlocksAPISerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        request_data = serializer.validated_data
        user_message = ""

        #check hard limit
        if request_data['to_block'] is True and UserBlocks.objects.filter(user=request.user).count() >= settings.USER_BLOCKS_LIMIT:

            return Response(
                data={
                    'message': 'You have reached the limit for who you can block. Consider unblocking someone.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #get target user
        target_user = get_object_or_404(get_user_model(), username_lowercase=request_data['username'].lower())

        #disallow users from blocking themselves
        if target_user.id == request.user.id:

            return Response(
                data={
                    'message': 'You cannot block yourself.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if request_data['to_block'] is True:

            #handle blocking
            UserBlocks.objects.get_or_create(
                user=request.user,
                blocked_user=target_user
            )

            user_message = "You have blocked " + target_user.username + "."

        else:

            #handle unblocking
            UserBlocks.objects.filter(
                user=request.user,
                blocked_user=target_user
            ).delete()

            user_message = "You have unblocked " + target_user.username + "."

        #update when was the last time user has took action via this POST API

        when_last_action_s = math.trunc(get_datetime_now().timestamp())

        cache.set(
            self.determine_when_last_action_s_cache_key(self.request.user.id),
            when_last_action_s,
        )

        return Response(
            data={
                'message': user_message,
            },
            status=status.HTTP_200_OK
        )



class UserFollowsAPI(generics.GenericAPIView):

    serializer_class = UserFollowsSerializer
    permission_classes = [IsAuthenticated]


    def determine_when_last_action_s_cache_key(self, user_id:int):

        return 'user_follows_when_last_action_s_' + str(user_id)


    #can only get user's own following list
    def get(self, request, *args, **kwargs):

        #ensure cache exists

        when_last_action_s = cache.get(self.determine_when_last_action_s_cache_key(self.request.user.id), None)

        if when_last_action_s is None:

            latest_row = None

            try:

                latest_row = UserFollows.objects.filter(user=self.request.user).latest('when_created')

                #proceeds to fetching all rows

            except UserFollows.DoesNotExist:

                #early detection of 0 rows in db
                #ensure cache exists so subsequent requests with no new actions won't query db again

                when_last_action_s = math.trunc(get_datetime_now().timestamp())

                cache.set(
                    self.determine_when_last_action_s_cache_key(self.request.user.id),
                    when_last_action_s
                )

                #already know 0 rows in db, so return
                return Response(
                    data={
                        'data': [],
                        'when_last_action_s': when_last_action_s,
                    },
                    status=status.HTTP_200_OK
                )

            when_last_action_s = math.trunc(latest_row.when_created.timestamp())

            cache.set(
                self.determine_when_last_action_s_cache_key(self.request.user.id),
                when_last_action_s
            )

        #check if frontend wants to check for sync
        #do comparison via math.trunc() value of datetime.timestamp(), i.e. seconds since UNIX epoch, a.k.a. posix

        passed_when_last_action_s = self.request.GET.get('when_last_action_s', None)

        if passed_when_last_action_s is not None:

            #validate

            try:

                passed_when_last_action_s = int(passed_when_last_action_s)

            except:

                return Response(
                    data={
                        'message': "Invalid when_last_action_s passed.",
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            

            #check if frontend is in sync with cache

            if passed_when_last_action_s == when_last_action_s:

                #frontend and cache are up-to-date

                return Response(
                    data={
                        'data': [],
                        'is_up_to_date': True,
                    },
                    status=status.HTTP_200_OK
                )

        #not in sync, or frontend does not care
        #continue with fetching rows

        #for something as simple as only requiring 1 column, serializing and returning as {} for every row is overkill
        #test results at 1000 rows via Content-Length header: serializer (66900 bytes), list (18900 bytes)
        #also confirmed via self.assertNumQueries(1) at test for queryset below

        result = UserFollows.objects.select_related('followed_user').filter(user=request.user).order_by('when_created').values_list('followed_user__username')

        usernames = []

        #transform tuple-per-object into list

        for row in result:

            usernames.append(row[0])

        response = Response(
            data={
                'data': usernames,
                'when_last_action_s': when_last_action_s
            },
            status=status.HTTP_200_OK
        )

        patch_cache_control(
            response,
            no_cache=True, no_store=True, must_revalidate=True, max_age=0
        )

        return response


    #perform following/unfollowing
    @method_decorator(app_decorators.deny_if_banned("response"))
    def post(self, request, *args, **kwargs):

        #wanted to allow for bulk changes via usernames=[...], but it is overkill for what this feature is
        #initially also returned when_last_action_s
            #but it can give frontend a false confirmation of sync if frontend performs POST with outdated store
            #therefore, POST no longer returns when_last_action_s

        serializer = PostUserFollowsAPISerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        request_data = serializer.validated_data
        user_message = ""

        #check hard limit
        if request_data['to_follow'] is True and UserFollows.objects.filter(user=request.user).count() >= settings.USER_FOLLOWS_LIMIT:

            return Response(
                data={
                    'message': 'You have reached the limit for who you can follow. Consider unfollowing someone.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #get target user
        target_user = get_object_or_404(get_user_model(), username_lowercase=request_data['username'].lower())

        #disallow users from following themselves
        if target_user.id == request.user.id:

            return Response(
                data={
                    'message': 'You cannot follow yourself.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if request_data['to_follow'] is True:

            #handle following
            UserFollows.objects.get_or_create(
                user=request.user,
                followed_user=target_user
            )

            user_message = "You have followed " + target_user.username + "."

        else:

            #handle unfollowing
            UserFollows.objects.filter(
                user=request.user,
                followed_user=target_user
            ).delete()

            user_message = "You have unfollowed " + target_user.username + "."

        #update when was the last time user has took action via this POST API

        when_last_action_s = math.trunc(get_datetime_now().timestamp())

        cache.set(
            self.determine_when_last_action_s_cache_key(self.request.user.id),
            when_last_action_s,
        )

        return Response(
            data={
                'message': user_message,
            },
            status=status.HTTP_200_OK
        )



class AudioClipTonesAPI(generics.GenericAPIView):

    serializer_class = AudioClipTonesSerializer
    permission_classes = []


    def get(self, request, *args, **kwargs):

        audio_clip_tones = None

        try:

            sentinel = object()

            audio_clip_tones = cache.get("all_audio_clip_tones", default=sentinel)

            if audio_clip_tones is sentinel:

                #does not exist in cache
                #retrieve and store in cache

                audio_clip_tones = AudioClipTones.objects.all()

                list(audio_clip_tones)

                cache.set(
                    "all_audio_clip_tones",
                    audio_clip_tones,
                    timeout=settings.CACHE_AUDIO_CLIP_TONE_AGE_S,
                )

        except ConnectionError:

            #fallback for when Redis is down
            audio_clip_tones = AudioClipTones.objects.all()

        except Exception as e:

            raise e

        response = Response(
            data={
                'data': AudioClipTonesSerializer(
                    audio_clip_tones,
                    many=True
                ).data
            }
        )

        patch_cache_control(
            response,
            no_cache=False, no_store=False, must_revalidate=True, max_age=settings.CACHE_AUDIO_CLIP_TONE_AGE_S
        )

        return response



class GetEventsAPI(generics.GenericAPIView):

    serializer_class = EventsAndAudioClipsAPISerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


    def get_events_by_id(self, event_id):

        #to check whether event__eventreplyqueues has rows, use hasattr(audio_clips[0].event, 'eventreplyqueues')

        audio_clips = AudioClips.objects.prefetch_related(
            'audio_clip_role',
            'event',
            'event__generic_status',
            #join any event_reply_queue row to event, not the normal FK prefetch
            Prefetch(
                'event__eventreplyqueues',
                EventReplyQueues.objects.filter(
                    locked_for_user_id=self.request.user.id,
                    event_id=event_id,
                ),
            ),
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
                audio_clip_likes_dislikes.is_liked AS is_liked_by_user,
                audio_clip_metrics.like_count AS like_count,
                audio_clip_metrics.dislike_count AS dislike_count
            FROM audio_clips
            LEFT JOIN events ON audio_clips.event_id = events.id
            LEFT JOIN audio_clip_tones ON audio_clips.audio_clip_tone_id = audio_clip_tones.id
            LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id
                AND audio_clip_likes_dislikes.user_id = %s
            LEFT JOIN audio_clip_metrics ON audio_clips.id = audio_clip_metrics.audio_clip_id
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

        serializer = GetEventsAPISerializer(data=kwargs)

        if serializer.is_valid() is False:

            return Response(
                data={
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        audio_clips = self.get_events_by_id(serializer.validated_data['event_id'])

        #check if there are rows
        #can have no rows when originator is reuploading

        if len(audio_clips) == 0:

            return Response(
                data={
                    'data': [],
                },
                status=status.HTTP_200_OK
            )

        #has audio_clips

        events_and_audio_clips = []

        #we have event.eventreplyqueues if request.user has queued or is replying

        if hasattr(audio_clips[0].event, 'eventreplyqueues') is True:

            event_reply_queues = extract_event_reply_queues_once_per_event(audio_clips)

            events_and_audio_clips = LockedEventsAndAudioClipsAPISerializer(
                group_audio_clips_into_events_and_event_reply_queues(audio_clips, event_reply_queues),
                many=True,
            ).data

        else:

            events_and_audio_clips = EventsAndAudioClipsAPISerializer(
                group_audio_clips_into_events(audio_clips),
                many=True,
            ).data

        response = Response(
            data={
                'data': events_and_audio_clips,
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



#UserFollows has no effect here
    #if it should, then have a separate query, and join after
class BrowseEventsAPI(generics.GenericAPIView):

    serializer_class = EventsAndAudioClipsAPISerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


    def list_latest_grouped_audio_clips(
        self,
        username:str='',
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

        #due to cursor-based browsing requiring 1 fixed direction for ordering,
        #it is impossible to do "back" without providing cursor_token
        if next_or_back == 'back' and cursor_token == '':

            return result

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
                    __name__,
                    user_message="Unable to fetch content due to faulty cursor token.",
                    dev_message="Token could not be decoded: " + cursor_token
                )

        #handle whether to display all audio_clip_tones, or specific

        audio_clip_tones_sql = ''
        audio_clip_tones_params = []

        if audio_clip_tone_id is not None:

            audio_clip_tones_sql = '''
                AND audio_clips.audio_clip_tone_id = %s
            '''
            audio_clip_tones_params = [audio_clip_tone_id]

        #prepare timeframe

        datetime_between = get_datetime_between('all')

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

        user_sql = ''
        user_join_sql = ''
        user_params = []

        if username_lowercase != '':

            user_sql = '''
                AND audio_clips.user_id = (
                    SELECT id FROM voicewake_user
                    WHERE username_lowercase = %s
                )
            '''

            user_join_sql = '''
                INNER JOIN voicewake_user ON audio_clips.user_id = voicewake_user.id
            '''
            user_params.append(username_lowercase)

        #handle event generic_status

        event_generic_status_name_sql = ''

        if username_lowercase != '':

            if audio_clip_role_name == 'originator':

                #for originator, show incomplete and completed for profile page
                event_generic_status_name_sql = '''
                    AND events.generic_status_id IN (
                        SELECT id FROM generic_statuses WHERE generic_status_name IN ('incomplete', 'completed')
                    )
                '''

            elif audio_clip_role_name == 'responder':

                #show completed, but also deleted
                event_generic_status_name_sql = '''
                    AND events.generic_status_id IN (
                        SELECT id FROM generic_statuses WHERE generic_status_name IN ('completed', 'deleted')
                    )
                '''

        else:

            event_generic_status_name_sql = '''
                AND events.generic_status_id = (
                    SELECT id FROM generic_statuses WHERE generic_status_name = 'completed'
                )
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
            target_events AS (
                SELECT
                    audio_clips.event_id, audio_clips.when_created, audio_clips.id
                FROM audio_clips
                INNER JOIN events ON audio_clips.event_id = events.id
                WHERE audio_clips.is_banned IS FALSE

                ''' + audio_clip_tones_sql + '''

                AND audio_clips.generic_status_id = (
                    SELECT id FROM generic_statuses
                    WHERE generic_status_name = %s
                )
                AND audio_clips.audio_clip_role_id = (
                    SELECT id FROM audio_clip_roles
                    WHERE audio_clip_role_name = %s
                )
                AND audio_clips.when_created BETWEEN %s AND %s

                ''' + event_generic_status_name_sql + '''
                ''' + user_sql + '''

                ''' + cursor_sql + '''
                ''' + cursor_order_sql + '''

                LIMIT %s
            )
            SELECT audio_clips.*,

            ''' + is_liked_by_user_sql['col'] + ''',
            audio_clip_metrics.like_count AS like_count,
            audio_clip_metrics.dislike_count AS dislike_count

            FROM audio_clips
            RIGHT JOIN target_events ON audio_clips.event_id = target_events.event_id
            LEFT JOIN audio_clip_metrics ON audio_clips.id = audio_clip_metrics.audio_clip_id
            INNER JOIN generic_statuses AS ac_gs ON audio_clips.generic_status_id = ac_gs.id
            INNER JOIN audio_clip_roles ON audio_clips.audio_clip_role_id = audio_clip_roles.id

            ''' + user_join_sql + '''
            ''' + is_liked_by_user_sql['join'] + '''

            WHERE audio_clips.is_banned IS FALSE

            AND ac_gs.generic_status_name = %s
            ''' + order_sql + '''
        '''

        full_params = audio_clip_tones_params + [
            'ok',
            audio_clip_role_name,
            datetime_between['datetime_from'],
            datetime_between['datetime_to'],
        ] + user_params + cursor_params + [
            settings.EVENT_QUANTITY_PER_PAGE,
        ] + is_liked_by_user_params + [
            'ok',
        ] + order_params

        #execute

        #all must be prefetch_related, otherwise serializer re-fetches on a per-row basis (many extra queries)
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

        if len(audio_clips) == 0:

            return result
        
        result['rows'] = audio_clips

        #start preparing our cursor tokens
        #our desired audio_clip_role_name + username is always grouped to the first half

        result['back_cursor_token'] = encode_cursor_token({
            'when_created': audio_clips[0].when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
            'id': audio_clips[0].id,
        })

        last_index = 0

        for x in range(0, len(audio_clips)):

            if audio_clips[x].audio_clip_role.audio_clip_role_name == audio_clip_role_name:

                #edge case awareness
                #cursor is most accurate when at least 1 row with specified audio_clip_role_name is guaranteed to exist
                last_index = x

            else:

                break

        result['next_cursor_token'] = encode_cursor_token({
            'when_created': audio_clips[last_index].when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
            'id': audio_clips[last_index].id,
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


    #ready to handle any user's likes/dislikes, but frontend isn't, so can only view own likes/dislikes for now
    #frontend shall accept "deleted" event, but audio_clips must always be "ok", to ensure 1:1 originator:responder
    def list_latest_liked_disliked_audio_clips(
        self,
        username:str,
        likes_or_dislikes:Literal['likes', 'dislikes']='likes',
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

        #due to cursor-based browsing requiring 1 fixed direction for ordering,
        #it is impossible to do "back" without providing cursor_token
        if next_or_back == 'back' and cursor_token == '':

            return result

        username_lowercase = username.lower()
        is_liked = True if likes_or_dislikes == 'likes' else False

        #handle cursor token

        decoded_cursor_token = {}
        cursor_params = []

        if cursor_token != '':

            try:

                #get audio_clips.when_created, audio_clips.id
                decoded_cursor_token = decode_cursor_token(cursor_token)

                cursor_params = [
                    decoded_cursor_token['last_modified'],
                    decoded_cursor_token['id'], decoded_cursor_token['last_modified'],
                ]

            except:

                raise custom_error(
                    ValueError,
                    __name__,
                    user_message="Unable to fetch content due to faulty cursor token.",
                    dev_message="Token could not be decoded: " + cursor_token
                )

        #handle whether to display all audio_clip_tones, or specific

        audio_clip_tones_sql = ''
        audio_clip_tones_params = []

        if audio_clip_tone_id is not None:

            audio_clip_tones_sql = '''
                AND ac.audio_clip_tone_id = %s
            '''
            audio_clip_tones_params.append(audio_clip_tone_id)

        #prepare adjustments based on cursor direction

        cursor_sql = ''
        cursor_order_sql = ''

        if next_or_back == 'next':

            if len(decoded_cursor_token) > 0:

                cursor_sql = '''
                    AND (
                        acld.last_modified <= %s
                        AND
                        (acld.id < %s OR acld.last_modified < %s)
                    )
                '''

            cursor_order_sql = '''ORDER BY acld.last_modified DESC, acld.id DESC'''

        elif next_or_back == 'back':

            if len(decoded_cursor_token) > 0:

                cursor_sql = '''
                    AND (
                        acld.last_modified >= %s
                        AND
                        (acld.id > %s OR acld.last_modified > %s)
                    )
                '''

            cursor_order_sql = '''ORDER BY acld.last_modified ASC, acld.id ASC'''

        #handle event generic_status

        event_generic_status_name_sql = ''

        if audio_clip_role_name == 'originator':

            #allow events of incomplete/completed/deleted
            event_generic_status_name_sql = '''
                AND e.generic_status_id IN (
                    SELECT id FROM generic_statuses
                    WHERE generic_status_name IN ('incomplete', 'completed', 'deleted')
                )
            '''

        elif audio_clip_role_name == 'responder':

            #allow events of completed/deleted
            event_generic_status_name_sql = '''
                AND e.generic_status_id IN (
                    SELECT id FROM generic_statuses
                    WHERE generic_status_name IN ('completed', 'deleted')
                )
            '''

        #get audio_clips
        #only allow "ok" audio_clips to ensure 1:1, as there can be 1 originator, 2 deleted responders, 1 responder

        full_sql = '''
            WITH target_events AS (
                SELECT ac.id AS ac_id, ac.event_id AS ac_event_id,
                    acld.last_modified AS acld_last_modified, acld.id AS acld_id
                FROM audio_clip_likes_dislikes AS acld
                INNER JOIN audio_clips AS ac ON acld.audio_clip_id = ac.id
                INNER JOIN events AS e ON ac.event_id = e.id

                WHERE ac.is_banned IS FALSE
                AND acld.user_id = (
                    SELECT id FROM voicewake_user WHERE username_lowercase = %s
                )
                AND ac.audio_clip_role_id = (
                    SELECT id FROM audio_clip_roles WHERE audio_clip_role_name = %s
                )
                AND acld.is_liked = %s
                AND ac.generic_status_id = (
                    SELECT id FROM generic_statuses WHERE generic_status_name = %s
                )

                ''' + event_generic_status_name_sql + '''
                ''' + audio_clip_tones_sql + '''
                ''' + cursor_sql + '''
                ''' + cursor_order_sql + '''
                LIMIT %s
            )
            SELECT
                ac.*,
                acld.is_liked AS is_liked_by_user,
                target_events.acld_last_modified AS te_acld_last_modified,
                target_events.acld_id AS te_acld_id,
                audio_clip_metrics.like_count AS like_count,
                audio_clip_metrics.dislike_count AS dislike_count
            FROM audio_clips AS ac
            LEFT JOIN audio_clip_likes_dislikes AS acld ON ac.id = acld.audio_clip_id
            LEFT JOIN audio_clip_metrics ON ac.id = audio_clip_metrics.audio_clip_id
            INNER JOIN target_events ON ac.event_id = target_events.ac_event_id
            WHERE ac.is_banned IS FALSE
            AND acld.user_id = (
                SELECT id FROM voicewake_user WHERE username_lowercase = %s
            )
            AND ac.generic_status_id = (
                SELECT id FROM generic_statuses WHERE generic_status_name = %s
            )
            ORDER BY te_acld_last_modified DESC, te_acld_id DESC
        '''

        full_params = [
            username_lowercase,
            audio_clip_role_name,
            is_liked,
            'ok',
        ] + audio_clip_tones_params + [
        ] + cursor_params + [
            settings.EVENT_QUANTITY_PER_PAGE,
        ] + [
            username_lowercase,
            'ok',
        ]

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

        if len(audio_clips) == 0:

            return result

        #settle cursor
        #because we join by event_id via target_events, all rows will have our unique fields, i.e. no None

        result['back_cursor_token'] = encode_cursor_token({
            'last_modified': audio_clips[0].te_acld_last_modified.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
            'id': audio_clips[0].te_acld_id,
        })
        result['next_cursor_token'] = encode_cursor_token({
            'last_modified': audio_clips[-1].te_acld_last_modified.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
            'id': audio_clips[-1].te_acld_id,
        })

        result['rows'] = audio_clips

        return result

        #notes
            #when user has 110k likes and 110k dislikes, while having no matching audio_clip.audio_clip_role_id,
            #takes 660ms, as planner makes full index scan in this case


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

        request_data = serializer.validated_data

        #check if user is trying to view a user that does not exist

        username_lowercase = request_data['username'].lower()

        if len(username_lowercase) > 0 and get_user_model().objects.filter(username_lowercase=username_lowercase).exists() is False:

            return Response(
                data={
                    'message': 'Username does not exist.',
                },
                status=status.HTTP_404_NOT_FOUND
            )

        #check if user is trying to view audio_clip_tone that does not exist

        if request_data['audio_clip_tone_id'] is not None and AudioClipTones.objects.filter(id=request_data['audio_clip_tone_id']).exists() is False:

            return Response(
                data={
                    'message': 'Tone does not exist.',
                },
                status=status.HTTP_404_NOT_FOUND
            )

        #get rows and cursor
        #currently only handling latest

        result = None

        if request_data['likes_or_dislikes'] != '':

            #users can only view their own likes/dislikes for now

            if(
                request.user.is_authenticated is True and
                request.user.username_lowercase == username_lowercase
            ):

                result = self.list_latest_liked_disliked_audio_clips(
                    username=request_data['username'],
                    likes_or_dislikes=request_data['likes_or_dislikes'],
                    audio_clip_role_name=request_data['audio_clip_role_name'],
                    audio_clip_tone_id=request_data['audio_clip_tone_id'],
                    next_or_back=request_data['next_or_back'],
                    cursor_token=request_data['cursor_token'],
                )

            else:

                return Response(
                    data={
                        'message': 'You can only view your own likes and dislikes for now.',
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

        else:

            result = self.list_latest_grouped_audio_clips(
                username=request_data['username'],
                audio_clip_role_name=request_data['audio_clip_role_name'],
                audio_clip_tone_id=request_data['audio_clip_tone_id'],
                next_or_back=request_data['next_or_back'],
                cursor_token=request_data['cursor_token'],
            )

        #prepare next and back URLs
        #we used to return full URLs via self.request.build_absolute_uri().split(request_data['next_or_back'], 1)
        #but for localhost Docker, it would not include port in URL, causing frontend to fail

        next_token = ""
        back_token = ""

        if len(result['rows']) > 0:

            #if we have > 0 rows, even with 1 row, both next and back cursor tokens will exist
            next_token = result['next_cursor_token']
            back_token = result['back_cursor_token']

        elif len(result['rows']) == 0 and request_data['cursor_token'] != '':

            #reuse passed cursor token, if any
            next_token = request_data['cursor_token']
            back_token = request_data['cursor_token']

        #build the response

        response_data = group_audio_clips_into_events(result['rows'])
        response_data = EventsAndAudioClipsAPISerializer(
            response_data,
            many=True,
        ).data

        response = Response(
            data={
                'next_token': next_token,
                'back_token': back_token,
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



#does not have own get(), since viewing audio_clips always involves parent events
#handle creating audio_clips
    #if audio_clip_role_name='originator', create event
    #if audio_clip_role_name='responder', link to event and reset lock
class CreateEventsAPI(generics.GenericAPIView):

    serializer_class = CreateAudioClips_Upload_APISerializer
    permission_classes = [IsAuthenticated]
    available_contexts = ['upload', 'regenerate_upload_url', 'process']
    url_context:Literal['upload', 'regenerate_upload_url', 'process'] = 'upload'


    def __init__(self, *args, **kwargs):

        if 'url_context' not in kwargs or kwargs['url_context'] not in self.available_contexts:

            raise custom_error(
                ValueError,
                __name__,
                dev_message="Incorrect url_context. Check .as_view() at urls.py."
            )

        super().__init__(*args, **kwargs)


    @method_decorator([
        app_decorators.deny_if_no_username("response"),
        app_decorators.deny_if_banned("response"),
    ])
    def post(self, request, *args, **kwargs):

        serializer = None

        if self.url_context == 'upload':

            serializer = CreateAudioClips_Upload_APISerializer(
                data=request.data,
                many=False,
                context={
                    'audio_clip_role_name': 'originator',
                },
            )

        elif self.url_context == 'regenerate_upload_url':

            serializer = CreateAudioClips_Upload_RegenerateURL_APISerializer(
                data=request.data,
                many=False,
            )

        elif self.url_context == 'process':

            serializer = CreateAudioClips_Process_APISerializer(
                data=request.data,
                many=False,
            )

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        request_data = serializer.validated_data

        #proceed

        try:

            create_audio_clips_class = CreateAudioClips(
                user=self.request.user,
                is_ec2=settings.IS_EC2,
                url_context='create_event',
                unprocessed_file_extensions=settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS,
                processed_file_extension=os.environ['AUDIO_CLIP_PROCESSED_FILE_EXTENSION'],
                event_create_daily_limit=settings.EVENT_CREATE_DAILY_LIMIT,
                event_reply_daily_limit=settings.EVENT_REPLY_DAILY_LIMIT,
                event_reply_expiry_seconds=settings.EVENT_REPLY_MAX_DURATION_S,
            )

            if self.url_context == 'upload':

                return create_audio_clips_class.create_records_and_return_s3_endpoint_as_originator(
                    event_name=request_data['event_name'],
                    audio_clip_tone_id=request_data['audio_clip_tone_id'],
                    recorded_file_extension=request_data['recorded_file_extension'],
                )

            elif self.url_context == 'regenerate_upload_url':

                return create_audio_clips_class.regenerate_s3_endpoint(
                    audio_clip_id=request_data['audio_clip_id'],
                )

            elif self.url_context == 'process':

                error_response = create_audio_clips_class.start_normalisation(
                    audio_clip_id=request_data['audio_clip_id'],
                )

                if error_response is not None:

                    return error_response

                #add task to queue

                task_normalisation.s(
                    user_id=create_audio_clips_class.user.id,
                    processing_cache_key=create_audio_clips_class.processing_cache_key,
                    audio_clip_id=create_audio_clips_class.audio_clip.id,
                    event_id=create_audio_clips_class.event.id,
                ).delay()

                processing_cache_processing = create_audio_clips_class.get_processing_cache_processing_object(
                    create_audio_clips_class.processing_cache,
                    request_data['audio_clip_id']
                )

                return Response(
                    data={
                        'attempts_left': processing_cache_processing['attempts_left'],
                    },
                    status=status.HTTP_200_OK
                )

        except AudioClipTones.DoesNotExist:

            return Response(
                data={
                    'message': 'Your selected tag was not found. Try a different one.',
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:

            if get_user_message_from_custom_error(e) == "":

                #unknown error
                raise e

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )



#user can generate new event reply choice
    #will unlock previous is_replying=False event
    #will add to UserEvents when locking for is_replying=False
#UserFollows has no effect here
    #if it should, then have a separate query and join after, instead of doing it all in one query
#Events are not affected by lock/unlock for reply
class EventReplyChoicesAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = [IsAuthenticated]

    #excludes event started by user
    #excludes event that user has talked in before, e.g. talked and banned, etc.
    #excludes those that blocked user, as well as those that the user has blocked, i.e. goes both ways
    def get_audio_clips_by_incomplete_events(self, audio_clip_tone_id:int|None=None):

        #this must be balanced between "give older unreplied events a chance" and "new events get replied fast enough"
        oldest_when_created = (get_datetime_now() - timedelta(seconds=settings.EVENT_INCOMPLETE_QUEUE_MAX_AGE_S))
        oldest_when_created = oldest_when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z')

        #do not get events where this user has been involved in before
        #we select only events.id in selected_events, followed by events JOIN
        #because if we do events.* in selected_events, we'll have to write all columns in GROUP BY clause

        audio_clip_tone_sql = ''
        audio_clip_tone_params = []

        if audio_clip_tone_id is not None:

            audio_clip_tone_sql = '''
                AND audio_clips.audio_clip_tone_id = %s
            '''
            audio_clip_tone_params.append(audio_clip_tone_id)

        #doing "events.when_created >= datetime" is better, since with "<=", you'd need "restart search from latest" feature
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
				SELECT
                    audio_clips.*,
                    audio_clip_likes_dislikes.is_liked AS is_liked_by_user,
                    audio_clip_metrics.like_count AS like_count,
                    audio_clip_metrics.dislike_count AS dislike_count
                FROM audio_clips
                INNER JOIN events ON audio_clips.event_id = events.id
				LEFT JOIN event_reply_queues ON events.id = event_reply_queues.event_id
				LEFT JOIN excluded_events_1 ON events.id = excluded_events_1.event_id
				LEFT JOIN excluded_events_2 ON events.id = excluded_events_2.event_id
				LEFT JOIN excluded_users_1 ON audio_clips.user_id = excluded_users_1.id
				LEFT JOIN excluded_users_2 ON audio_clips.user_id = excluded_users_2.id
                LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id
                    AND audio_clip_likes_dislikes.user_id = %s
                LEFT JOIN audio_clip_metrics ON audio_clips.id = audio_clip_metrics.audio_clip_id
				WHERE audio_clips.is_banned IS FALSE
				''' + audio_clip_tone_sql + '''
				AND event_reply_queues.id IS NULL
				AND excluded_events_1.event_id IS NULL
				AND excluded_events_2.event_id IS NULL
				AND excluded_users_1.id IS NULL
				AND excluded_users_2.id IS NULL
				AND events.when_created >= %s
                AND audio_clips.audio_clip_role_id = (
                    SELECT id FROM audio_clip_roles
                    WHERE audio_clip_role_name = %s
                )
                AND audio_clips.generic_status_id = (
                    SELECT id FROM generic_statuses
                    WHERE generic_status_name = %s
                )
                AND events.generic_status_id = (
                    SELECT id FROM generic_statuses
                    WHERE generic_status_name = %s
                )
				LIMIT %s
        '''

        full_params = [
            self.request.user.id,
            self.request.user.id,
            self.request.user.id,
            self.request.user.id,
            self.request.user.id,
        ] + audio_clip_tone_params + [
            oldest_when_created,
            'originator',
            'ok',
            'incomplete',
            1,  #frontend currently can only handle 1
        ]

        #start
        audio_clips = AudioClips.objects.prefetch_related(
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

        #notes
            #would be great to do ORDER BY events.when_created ASC, but performance becomes terrible
                #index did not help
            #performant, tested with:
                #984 UserBlocks,
                #own 7650 incomplete events
                #some of UserBlocks have many incomplete/completed event


    #only to produce is_replying=False, i.e. choice
    #does not involve is_replying=True, a.k.a. replying
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
        #we do this here to encourage choosing the best audio_clip room,
        #while leaving the other good ones for other users
        prevent_events_from_queuing_twice_for_reply(
            self.request.user,
            bulk_events
        )

        #Events and EventReplyQueues are 1-to-1
        #originators and Events are also 1-to-1
        if len(audio_clips) != len(bulk_event_reply_queues):

            raise custom_error(
                ValueError,
                __name__,
                'Ratio of originators and EventReplyQueues is not 1-to-1 as expected.'
            )

        return bulk_event_reply_queues


    #involves both is_replying=False (choice) and is_replying=True (replying)
    #pass only_expired_rows=True for "first time searching in UI"
    #pass only_expired_rows=False for "skipped choice", "skipped replying"
    def unlock_all_locked_events(self, only_expired_rows:bool):

        #when user has lock, only new EventReplyQueues row is created
        #nothing is changed for event, hence, on unlocking, no need to deal with events

        datetime_now = get_datetime_now()

        if only_expired_rows is True:

            #is_replying=False

            when_locked_checkpoint = (
                datetime_now - timedelta(seconds=settings.EVENT_REPLY_CHOICE_MAX_DURATION_S)
            )

            EventReplyQueues.objects.filter(
                locked_for_user=self.request.user,
                is_replying=False,
                when_locked__lte=when_locked_checkpoint
            ).delete()

            #is_replying=True

            when_locked_checkpoint = (
                datetime_now - timedelta(seconds=settings.EVENT_REPLY_MAX_DURATION_S)
            )

            EventReplyQueues.objects.filter(
                locked_for_user=self.request.user,
                is_replying=True,
                when_locked__lte=when_locked_checkpoint
            ).delete()

        else:

            EventReplyQueues.objects.filter(
                locked_for_user=self.request.user,
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
            SELECT
                audio_clips.*,
                audio_clip_likes_dislikes.is_liked AS is_liked_by_user,
                audio_clip_metrics.like_count AS like_count,
                audio_clip_metrics.dislike_count AS dislike_count
            FROM audio_clips
			INNER JOIN event_reply_queues ON audio_clips.event_id = event_reply_queues.event_id
				AND event_reply_queues.locked_for_user_id = %s
            LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id
                AND audio_clip_likes_dislikes.user_id = %s
            LEFT JOIN audio_clip_metrics ON audio_clips.id = audio_clip_metrics.audio_clip_id
			WHERE audio_clips.is_banned IS FALSE
            AND audio_clips.generic_status_id = (
                SELECT id FROM generic_statuses
                WHERE generic_status_name = %s
            )
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

        serializer = EventReplyChoicesAPISerializer(data=request.data, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        request_data = serializer.validated_data

        #check whether user wants to auto-skip current choices and get new ones

        if request_data['unlock_all_locked_events'] is True:

            #auto-remove all locked events
            self.unlock_all_locked_events(only_expired_rows=False)

        elif request_data['unlock_all_locked_events'] is False:

            #auto-remove all locked events that are expired only
            self.unlock_all_locked_events(only_expired_rows=True)

            #since user still wants non-expired reply choices, we get, if any
            audio_clips = self.get_audio_clips_from_locked_events()
            event_reply_queues = extract_event_reply_queues_once_per_event(audio_clips)

            if len(audio_clips) > 0:

                #return non-expired reply choices
                result = group_audio_clips_into_events_and_event_reply_queues(audio_clips, event_reply_queues)
                serializer = LockedEventsAndAudioClipsAPISerializer(
                    result,
                    many=True,
                )

                return Response(
                    data={
                        'data': serializer.data,
                    },
                    status=status.HTTP_200_OK
                )

        #no existing reply choices, proceed

        try:

            create_audio_clips_class = CreateAudioClips(
                user=self.request.user,
                is_ec2=settings.IS_EC2,
                url_context='create_reply',
                unprocessed_file_extensions=settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS,
                processed_file_extension=os.environ['AUDIO_CLIP_PROCESSED_FILE_EXTENSION'],
                event_create_daily_limit=settings.EVENT_CREATE_DAILY_LIMIT,
                event_reply_daily_limit=settings.EVENT_REPLY_DAILY_LIMIT,
                event_reply_expiry_seconds=settings.EVENT_REPLY_MAX_DURATION_S,
            )

            #check reply daily limit

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

            audio_clips = self.get_audio_clips_by_incomplete_events(audio_clip_tone_id=request_data['audio_clip_tone_id'])

            if len(audio_clips) == 0:

                #no eligible events
                return Response(
                    data={
                        'data': [],
                    },
                    status=status.HTTP_200_OK
                )

            #lock events and get event_reply_queues
            event_reply_queues = self.lock_events_for_reply_choices(audio_clips)

            #return
            result = group_audio_clips_into_events_and_event_reply_queues(audio_clips, event_reply_queues)
            serializer = LockedEventsAndAudioClipsAPISerializer(
                result,
                many=True,
            )

            return Response(
                data={
                    'data': serializer.data,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:

            traceback.print_exc()

            if get_user_message_from_custom_error(e) == "":

                #unknown error
                raise e

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )



#purposely not check UserBlocks here
#else a few unnecessary edge cases must be dealt with, since blocking someone is spammable
class EventRepliesAPI(generics.GenericAPIView):

    serializer_class = EventRepliesAPISerializer
    permission_classes = [IsAuthenticated]
    available_contexts = [
        'start', 'cancel',
        'upload', 'regenerate_upload_url', 'process',
    ]
    url_context:Literal[
        'start', 'cancel',
        'upload', 'regenerate_upload_url', 'process',
    ] = 'start'


    def __init__(self, *args, **kwargs):

        if 'url_context' not in kwargs or kwargs['url_context'] not in self.available_contexts:

            raise custom_error(
                ValueError,
                __name__,
                dev_message="Incorrect url_context. Check .as_view() at urls.py."
            )

        super().__init__(*args, **kwargs)


    def _check_user_is_replying_in_other_events(self, excluded_event_id:int=None)->bool:

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


    def _unlock_reply_choices(self, excluded_event_id:int=None):

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
    def start_reply_in_event(self, event_id:int)->Response:

        #check if user is replying to any other event
        if self._check_user_is_replying_in_other_events(excluded_event_id=event_id) is True:

            return Response(
                data={
                    'message': 'You are already replying in a different event.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        #not yet replying to anything, proceed

        datetime_now = get_datetime_now()

        with transaction.atomic():

            #no 'try' here, let main call catch exception
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

                #event is no longer available
                target_event_reply_queue.delete()

                return Response(
                    data={
                        'message': 'This event is no longer available for reply.',
                        'can_retry': False,
                    },
                    status=status.HTTP_404_NOT_FOUND
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
                    status=status.HTTP_404_NOT_FOUND
                )

            #not yet expired, proceed

            #unlock other reply choices
            self._unlock_reply_choices(excluded_event_id=target_event_reply_queue.event_id)

            #user is officially replying
            target_event_reply_queue.when_locked = datetime_now
            target_event_reply_queue.is_replying = True
            target_event_reply_queue.save()

            serializer = EventReplyQueuesSerializer(
                target_event_reply_queue,
                many=False,
            )

            return Response(
                data={
                    'data': serializer.data,
                    'message': 'You are now replying in this event.',
                },
                status=status.HTTP_200_OK
            )


    #only delete if is_replying=True
    #only mark audio clip as deleted, and not actually delete, so we can enforce daily limit
    def cancel_reply_in_event(self, event_id:int)->Response:

        #no 'try' here, let main call catch exception

        delete_quantity, delete_quantity_by_model = EventReplyQueues.objects.filter(
            locked_for_user=self.request.user,
            event_id=event_id,
            is_replying=True
        ).delete()

        if delete_quantity == 0:

            raise EventReplyQueues.DoesNotExist

        #update audio clip and delete cache, if any

        audio_clip = None

        try:

            audio_clip = AudioClips.objects.select_related(
                'generic_status'
            ).get(
                user_id=self.request.user.id,
                event_id=event_id,
                audio_clip_role__audio_clip_role_name='responder',
            )

        except AudioClips.DoesNotExist:

            return Response(
                data={
                },
                status=status.HTTP_200_OK
            )
        
        #update audio_clip

        if audio_clip.generic_status.generic_status_name == 'processing':

            audio_clip.generic_status = GenericStatuses.objects.get(generic_status_name='deleted')
            audio_clip.save()

        #update cache

        processing_cache_key = CreateAudioClips.determine_processing_cache_key(user_id=self.request.user.id)

        processing_cache = cache.get(
            processing_cache_key,
            None
        )

        if processing_cache is None:

            return Response(
                data={
                },
                status=status.HTTP_200_OK
            )

        processing_cache_processing = CreateAudioClips.get_processing_cache_processing_object(
            processing_cache=processing_cache,
            audio_clip_id=audio_clip.id
        )

        if processing_cache_processing is not None:

            processing_cache['processings'].pop(str(audio_clip.id))

            CreateAudioClips.set_processing_cache(
                processing_cache_key=processing_cache_key,
                processing_cache=processing_cache
            )

        return Response(
            data={
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

        if self.url_context == 'start' or self.url_context == 'cancel':

            serializer = EventRepliesAPISerializer(data=request.data)

        elif self.url_context == 'upload':

            serializer = CreateAudioClips_Upload_APISerializer(
                data=request.data,
                context={
                    'audio_clip_role_name': 'responder',
                },
            )

        elif self.url_context == 'regenerate_upload_url':

            serializer = CreateAudioClips_Upload_RegenerateURL_APISerializer(data=request.data)

        elif self.url_context == 'process':

            serializer = CreateAudioClips_Process_APISerializer(data=request.data)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        request_data = serializer.validated_data

        #proceed

        try:

            create_audio_clips_class = None

            if self.url_context in ['upload', 'regenerate_upload_url', 'process']:

                create_audio_clips_class = CreateAudioClips(
                    user=self.request.user,
                    is_ec2=settings.IS_EC2,
                    url_context='create_reply',
                    unprocessed_file_extensions=settings.AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS,
                    processed_file_extension=os.environ['AUDIO_CLIP_PROCESSED_FILE_EXTENSION'],
                    event_create_daily_limit=settings.EVENT_CREATE_DAILY_LIMIT,
                    event_reply_daily_limit=settings.EVENT_REPLY_DAILY_LIMIT,
                    event_reply_expiry_seconds=settings.EVENT_REPLY_MAX_DURATION_S,
                )

            if self.url_context == "start":

                #start replying
                return self.start_reply_in_event(request_data['event_id'])

            elif self.url_context == 'upload':

                return create_audio_clips_class.create_records_and_return_s3_endpoint_as_responder(
                    event_id=request_data['event_id'],
                    audio_clip_tone_id=request_data['audio_clip_tone_id'],
                    recorded_file_extension=request_data['recorded_file_extension'],
                )


            elif self.url_context == 'regenerate_upload_url':

                return create_audio_clips_class.regenerate_s3_endpoint(
                    audio_clip_id=request_data['audio_clip_id'],
                )

            elif self.url_context == 'process':

                error_response = create_audio_clips_class.start_normalisation(
                    audio_clip_id=request_data['audio_clip_id'],
                )

                if error_response is not None:

                    return error_response

                #add task to queue

                task_normalisation.s(
                    user_id=create_audio_clips_class.user.id,
                    processing_cache_key=create_audio_clips_class.processing_cache_key,
                    audio_clip_id=create_audio_clips_class.audio_clip.id,
                    event_id=create_audio_clips_class.event.id,
                ).delay()

                processing_cache_processing = CreateAudioClips.get_processing_cache_processing_object(
                    processing_cache=create_audio_clips_class.processing_cache,
                    audio_clip_id=request_data['audio_clip_id']
                )

                return Response(
                    data={
                        'attempts_left': processing_cache_processing['attempts_left'],
                    },
                    status=status.HTTP_200_OK
                )

            elif self.url_context == "cancel":

                #delete event_reply_queue
                return self.cancel_reply_in_event(request_data['event_id'])

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
                    'can_retry': False,
                },
                status=status.HTTP_404_NOT_FOUND
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

            if get_user_message_from_custom_error(e) == "":

                #unknown error
                raise e

            return Response(
                data={
                    'message': get_user_message_from_custom_error(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )



#submit likes/dislikes
#is_liked=True/False, or destroy when undone
class AudioClipLikesDislikesAPI(generics.GenericAPIView):

    serializer_class = AudioClipLikesDislikesSerializer
    permission_classes = [IsAuthenticated]

    #no get() needed, since likes/dislikes are tied directly to audio_clips
    #still allow when audio_clip doesn't have generic_status "ok"
        #votes will matter when reassessed during repeated report, as well as allowing users to unlike deleted audio_clips

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

        request_data = serializer.validated_data

        #current code is also supposedly better than 100% delete + insert
        #https://stackoverflow.com/questions/1271641/in-sql-is-update-always-faster-than-deleteinsert

        #check if audio clip exists
        #need this check, for uncatchable update_or_create() exception during tests

        try:

            audio_clip = AudioClips.objects.select_related(
                'generic_status',
            ).get(
                pk=request_data['audio_clip_id'],
            )

            if audio_clip.generic_status.generic_status_name != 'ok' or audio_clip.generic_status.generic_status_name == 'deleted':

                return Response(
                    data={
                        'message': 'Recording is no longer available.',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except AudioClips.DoesNotExist:

            return Response(
                data={
                    'message': 'Recording does not exist.',
                },
                status=status.HTTP_404_NOT_FOUND
            )

        #start

        if request_data['is_liked'] is None:

            #handle removing like/dislike

            try:

                audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(
                    user=request.user,
                    audio_clip_id=request_data['audio_clip_id']
                )

                with transaction.atomic():

                    #should always exist
                    #don't catch error so system can log it
                    audio_clip_metric = AudioClipMetrics.objects.select_for_update().get(
                        audio_clip_id=request_data['audio_clip_id']
                    )

                    if audio_clip_like_dislike.is_liked is True:

                        audio_clip_metric.like_count -= 1

                    else:

                        audio_clip_metric.dislike_count -= 1

                    try:

                        audio_clip_metric.like_ratio = audio_clip_metric.like_count / (audio_clip_metric.like_count + audio_clip_metric.dislike_count)

                    except ZeroDivisionError:

                        audio_clip_metric.like_ratio = 0

                    audio_clip_metric.save()
                    audio_clip_like_dislike.delete()

            except AudioClipLikesDislikes.DoesNotExist:

                #allow frontend to handle race condition gracefully
                return Response(
                    data={
                    },
                    status=status.HTTP_200_OK
                )

        else:

            #handle new like/dislike

            audio_clip_like_dislike = None

            #don't use get_or_create(), because any existing row may be treated as "not found" when specifying is_liked
            #enables handling of request_data['is_liked']=True and row.is_liked=True, request_data['is_liked']=True and row.is_liked=False
            try:

                audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(
                    user=request.user,
                    audio_clip_id=request_data['audio_clip_id'],
                )

                #row exists with identical state
                #allow frontend to handle race condition gracefully

                if request_data['is_liked'] == audio_clip_like_dislike.is_liked:

                    return Response(
                        data={
                        },
                        status=status.HTTP_200_OK
                    )

                #change like/dislike

                with transaction.atomic():

                    #should always exist
                    #don't catch error so system can log it
                    audio_clip_metric = AudioClipMetrics.objects.select_for_update().get(
                        audio_clip_id=request_data['audio_clip_id']
                    )

                    if request_data['is_liked'] is True:

                        #change to like
                        audio_clip_like_dislike.is_liked = True
                        audio_clip_metric.like_count += 1
                        audio_clip_metric.dislike_count -= 1

                    else:

                        #change to dislike
                        audio_clip_like_dislike.is_liked = False
                        audio_clip_metric.like_count -= 1
                        audio_clip_metric.dislike_count += 1

                    try:

                        audio_clip_metric.like_ratio = audio_clip_metric.like_count / (audio_clip_metric.like_count + audio_clip_metric.dislike_count)

                    except ZeroDivisionError:

                        audio_clip_metric.like_ratio = 0

                    audio_clip_like_dislike.save()
                    audio_clip_metric.save()

            except AudioClipLikesDislikes.DoesNotExist:

                #handling this scenario is more straightforward
                #add new like/dislike

                audio_clip_like_dislike = AudioClipLikesDislikes.objects.create(
                    user=request.user,
                    audio_clip_id=request_data['audio_clip_id'],
                    is_liked=request_data['is_liked']
                )

                with transaction.atomic():

                    #should always exist
                    #don't catch error so system can log it
                    audio_clip_metric = AudioClipMetrics.objects.select_for_update().get(
                        audio_clip_id=request_data['audio_clip_id']
                    )

                    if audio_clip_like_dislike.is_liked is True:

                        #add like
                        audio_clip_metric.like_count += 1

                    else:

                        #add dislike
                        audio_clip_metric.dislike_count += 1

                    try:

                        audio_clip_metric.like_ratio = audio_clip_metric.like_count / (audio_clip_metric.like_count + audio_clip_metric.dislike_count)

                    except ZeroDivisionError:

                        audio_clip_metric.like_ratio = 0

                    audio_clip_metric.save()

        return Response(
            data={
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
            #cannot catch ForeignKeyViolation from update_or_create()
                #object will be created, end of line will be reached, status 200 is returned



class AudioClipProcessingsAPI(generics.GenericAPIView):

    serializer_class = CheckAudioClipProcessingsAPISerializer
    permission_classes = [IsAuthenticated]
    available_contexts = ['list', 'check', 'delete']
    url_context:Literal['list', 'check', 'delete'] = 'check'
    processing_statuses = ['processing', 'processed', 'not_found', 'lambda_error']


    #will minimally validate, no invalidation
    def check_normalisation_status(self, processing_cache:dict, audio_clip_id:int, return_type:Literal['string', 'response'])->str|Response:

        #do not create or modify anything here
        #404 if no longer available
        #409 if is processing
        #200 if processing is successful/failed

        if return_type not in ['string', 'response']:

            raise custom_error(
                ValueError,
                __name__,
                dev_message='Invalid return_type.',
            )

        processing_cache_processing = None

        if processing_cache is not None:

            processing_cache_processing = CreateAudioClips.get_processing_cache_processing_object(
                processing_cache=processing_cache,
                audio_clip_id=audio_clip_id
            )

        #409 if processing
        #when cache is not yet created,
        #it is when normalisation is just about to start

        if processing_cache_processing is not None:

            response_status = None

            if processing_cache_processing['is_processing'] is True:

                response_status = status.HTTP_409_CONFLICT

            else:

                response_status = status.HTTP_200_OK

            #still has attempts
            #frontend will track attempts_left
            #so if this returns -1 than what is at frontend, means processing failed

            if return_type == 'string':

                if processing_cache_processing['is_processing'] is True:

                    return 'processing'

                else:

                    return 'lambda_error'

            else:

                return Response(
                    data={
                        'is_processing': processing_cache_processing['is_processing'],
                        'attempts_left': processing_cache_processing['attempts_left'],
                    },
                    status=response_status
                )

        #no cache, continue to check db

        target_audio_clip = None

        try:

            target_audio_clip = AudioClips.objects.select_related(
                'generic_status',
            ).get(
                pk=audio_clip_id,
                user_id=self.request.user.id,
            )

        except AudioClips.DoesNotExist:

            if return_type == 'string':

                return 'not_found'

            else:

                return Response(
                    data={
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

        #check

        if target_audio_clip.generic_status.generic_status_name == 'ok':

            if return_type == 'string':

                return 'processed'
            
            else:

                return Response(
                    data={
                        'is_processed': True
                    },
                    status=status.HTTP_200_OK
                )

        if return_type == 'string':

            return 'not_found'

        else:

            return Response(
                data={
                },
                status=status.HTTP_404_NOT_FOUND
            )


    def __init__(self, *args, **kwargs):

        #self.request is not available here

        if 'url_context' not in kwargs or kwargs['url_context'] not in self.available_contexts:

            raise custom_error(
                ValueError,
                __name__,
                dev_message="Incorrect url_context. Check .as_view() at urls.py."
            )

        super().__init__(*args, **kwargs)


    @method_decorator(app_decorators.deny_if_banned("response"))
    def get(self, request, *args, **kwargs):

        #list is just to sync data at frontend
        #keep list and check separate, to allow us to check only specific processings as desired

        if self.url_context == 'check':

            serializer = CheckAudioClipProcessingsAPISerializer(data=kwargs)

            if serializer.is_valid() is False:

                return Response(
                    data={
                        'message': get_serializer_error_message(serializer),
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            request_data = serializer.validated_data

            processing_cache_key = CreateAudioClips.determine_processing_cache_key(user_id=request.user.id)
            processing_cache = cache.get(processing_cache_key, None)

            #ensure main cache exists
            if processing_cache is None:

                processing_cache = CreateAudioClips.get_default_processing_cache_main_object()
                cache.set(processing_cache_key, processing_cache, timeout=settings.REDIS_AUDIO_CLIP_PROCESSING_CACHE_EXPIRY_S)

            return self.check_normalisation_status(
                processing_cache=processing_cache,
                audio_clip_id=request_data['audio_clip_id'],
                return_type='response'
            )

        elif self.url_context == 'list':

            #TODO: consider listing qualified audio_clips from db first, to ensure cache stays true to source of truth
            #wouldn't want simple cache unavailability to cause people to lose track of processing clips
            #to reduce load on db, maybe use time-based sync

            processing_cache_key = CreateAudioClips.determine_processing_cache_key(user_id=request.user.id)
            processing_cache = cache.get(processing_cache_key, None)

            #ensure main cache exists
            if processing_cache is None:

                processing_cache = CreateAudioClips.get_default_processing_cache_main_object()
                cache.set(processing_cache_key, processing_cache, timeout=settings.REDIS_AUDIO_CLIP_PROCESSING_CACHE_EXPIRY_S)

            #add "status" to processing

            for audio_clip_id in processing_cache['processings']:

                processing_status = self.check_normalisation_status(
                    processing_cache=processing_cache,
                    audio_clip_id=int(audio_clip_id),
                    return_type='string'
                )

                if processing_status not in self.processing_statuses:

                    raise custom_error(
                        ValueError,
                        __name__,
                        dev_message="Invalid status.",
                    )

                processing_cache['processings'][str(audio_clip_id)].update({
                    'status': processing_status
                })

            final_data = ListAudioClipProcessingsAPISerializer(processing_cache).data

            return Response(
                data={
                    'data': final_data,
                },
                status=status.HTTP_200_OK,
            )

        else:

            return Response(
                data={
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )


    @method_decorator(app_decorators.deny_if_banned("response"))
    def post(self, request, *args, **kwargs):

        if self.url_context != 'delete':

            return Response(
                data={
                },
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        serializer = DeleteAudioClipProcessingsAPISerializer(data=request.data)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        request_data = serializer.validated_data

        #delete from audio_clip, event_reply_queue, and cache

        audio_clip = None

        try:

            audio_clip = AudioClips.objects.select_related('audio_clip_role').get(
                pk=request_data['audio_clip_id'],
                user_id=request.user.id,
                generic_status__generic_status_name='processing'
            )

        except AudioClips.DoesNotExist:

            return Response(
                data={
                },
                status=status.HTTP_404_NOT_FOUND
            )

        #start deleting

        #delete queue, if responder

        if audio_clip.audio_clip_role.audio_clip_role_name == 'responder':

            EventReplyQueues.objects.filter(
                locked_for_user_id=request.user.id,
                event_id=audio_clip.event_id,
                is_replying=True,
            ).delete()

        #delete processing from cache

        processing_cache_key = CreateAudioClips.determine_processing_cache_key(user_id=request.user.id)
        processing_cache = cache.get(processing_cache_key, None)

        if processing_cache is None:

            #if unexpectedly no cache, auto-create

            processing_cache = CreateAudioClips.get_default_processing_cache_main_object()

            cache.set(processing_cache_key, processing_cache, timeout=settings.REDIS_AUDIO_CLIP_PROCESSING_CACHE_EXPIRY_S)

        processing_cache_processing = CreateAudioClips.get_processing_cache_processing_object(
            processing_cache=processing_cache,
            audio_clip_id=audio_clip.id
        )

        if processing_cache_processing is not None:

            processing_cache['processings'].pop(str(audio_clip.id))

            CreateAudioClips.set_processing_cache(
                processing_cache_key=processing_cache_key,
                processing_cache=processing_cache
            )

        #delete event for originators

        if audio_clip.audio_clip_role.audio_clip_role_name == 'originator':

            #we can delete event early because we've implemented CASCADE
            Events.objects.filter(pk=audio_clip.event.id).delete()

        #delete audio_clip

        audio_clip.delete()

        return Response(
            data={
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
        
        request_data = serializer.validated_data

        try:

            #get audio_clip
            target_audio_clip = AudioClips.objects.select_related(
                'generic_status',
            ).get(
                pk=request_data['audio_clip_id'],
            )

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

        #check if audio_clip is eligible to be reported
        #e.g. cannot report when still processing and not shown publicly
        if target_audio_clip.generic_status.generic_status_name != 'ok':

            return Response(
                data={
                    'message': 'Recording does not exist.',
                },
                status=status.HTTP_404_NOT_FOUND
            )

        #add report
        AudioClipReports.objects.update_or_create(
            audio_clip_id=request_data['audio_clip_id'],
            defaults={
                "last_reported": get_datetime_now(),
            },
        )

        #for edge case where same user reports --> evaluated --> reports again,
        #no need to do anything, otherwise our cronjob can get overwhelmed

        return Response(
            data={
                'message': 'The recording is now queued for evaluation.',
            },
            status=status.HTTP_200_OK
        )



class AudioClipBansAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = [IsAuthenticated]

    #no post() here, cronjob does the banning
    #due to exponential ban period, banned audio_clips per user is nearly guaranteed to be low

    #banned users can get their own banned audio_clips
    def get(self, request, *args, **kwargs):

        #only allow users to use API if currently banned
        if request.user.banned_until is None:

            return Response(
                data={
                    'message': 'You can only view your banned recordings while you are banned.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        banned_audio_clips = AudioClips.objects.select_related(
            'audio_clip_role',
            'audio_clip_tone',
            'generic_status',
        ).filter(user=request.user, is_banned=True).order_by('-last_modified')

        serializer = AudioClipsSerializer(
            banned_audio_clips,
            many=True,
        )

        return Response(
            data={
                'data': serializer.data,
            },
            status=status.HTTP_200_OK
        )


    @method_decorator(app_decorators.deny_if_not_superuser("response"))
    def post(self, request, *args, **kwargs):

        serializer = PostAudioClipBansAPISerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        request_data = serializer.validated_data

        generic_status_incomplete = GenericStatuses.objects.get(generic_status_name='incomplete')
        generic_status_completed = GenericStatuses.objects.get(generic_status_name='completed')
        generic_status_deleted = GenericStatuses.objects.get(generic_status_name='deleted')

        audio_clip = None

        try:

            with transaction.atomic():

                audio_clip = AudioClips.objects.select_for_update(of=('self',)).select_related(
                    'audio_clip_role',
                    'event',
                    'user',
                    'generic_status',
                ).get(
                    pk=request_data['audio_clip_id'],
                )

                if audio_clip.user.id == request.user.id:

                    return Response(
                        data={
                            'message': 'You cannot ban yourself.',
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if audio_clip.generic_status.generic_status_name == 'deleted':

                    if audio_clip.is_banned is True:

                        #already banned
                        return Response(
                            data={
                                'message': 'Recording has been banned.',
                            },
                            status=status.HTTP_200_OK
                        )

                    else:

                        #can continue to ban "deleted" with is_banned=False
                        pass

                elif audio_clip.generic_status.generic_status_name != 'ok':

                    #not qualified for ban
                    return Response(
                        data={
                            'message': 'Recording not eligible for ban.',
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                #allow to proceed when "deleted" and is_banned=False
                #allow to proceed when "ok"

                audio_clip.is_banned = True
                audio_clip.generic_status = generic_status_deleted
                audio_clip.save()

                #remove relevant rows

                EventReplyQueues.objects.filter(event=audio_clip.event).delete()
                AudioClipLikesDislikes.objects.filter(audio_clip=audio_clip).delete()
                AudioClipMetrics.objects.filter(audio_clip=audio_clip).update(like_count=0, dislike_count=0, like_ratio=0)

                #handle event

                if audio_clip.audio_clip_role.audio_clip_role_name == 'originator':

                    #for originator, event always becomes 'deleted'
                    audio_clip.event.generic_status = generic_status_deleted
                    audio_clip.event.save()

                elif (
                    audio_clip.audio_clip_role.audio_clip_role_name == 'responder' and
                    audio_clip.event.generic_status_id == generic_status_completed.id
                ):

                    #for responder, event changes from 'completed' to 'incomplete'
                    audio_clip.event.generic_status = generic_status_incomplete
                    audio_clip.event.save()

                #ban user

                ban_days = settings.CRONJOB_AUDIO_CLIP_BAN_DAYS ** audio_clip.user.ban_count

                #cap ban_days, else it can get out of hand
                if ban_days > settings.CRONJOB_AUDIO_CLIP_MAX_BAN_DAYS:

                    ban_days = settings.CRONJOB_AUDIO_CLIP_MAX_BAN_DAYS

                audio_clip.user.ban_count += 1
                audio_clip.user.banned_until = get_datetime_now() + timedelta(days=ban_days)
                audio_clip.user.save()

                return Response(
                    data={
                        'message': 'Recording has been banned.',
                    },
                    status=status.HTTP_200_OK
                )

        except AudioClips.DoesNotExist:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_404_NOT_FOUND
            )



class AudioClipDeletionsAPI(generics.DestroyAPIView):

    serializer_class = None
    permission_classes = [IsAuthenticated]


    @method_decorator(app_decorators.deny_if_banned("response"))
    def delete(self, request, *args, **kwargs):

        #allow if user performing the action is superuser or is the one who created the audio_clip

        serializer = DeleteAudioClipDeletionsAPISerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        request_data = serializer.validated_data

        generic_status_incomplete = GenericStatuses.objects.get(generic_status_name='incomplete')
        generic_status_completed = GenericStatuses.objects.get(generic_status_name='completed')
        generic_status_deleted = GenericStatuses.objects.get(generic_status_name='deleted')

        audio_clip = None

        try:

            with transaction.atomic():

                audio_clip = AudioClips.objects.select_for_update(of=('self',)).select_related(
                    'audio_clip_role',
                    'event',
                ).get(
                    pk=request_data['audio_clip_id'],
                    generic_status__generic_status_name='ok',
                )

                if request.user.is_superuser is True or request.user.id == audio_clip.user_id:

                    audio_clip.generic_status = generic_status_deleted
                    audio_clip.save()

                else:

                    return Response(
                        data={
                            'message': 'You do not have permission to perform this action.',
                        },
                        status=status.HTTP_403_FORBIDDEN
                    )

                #remove relevant rows

                EventReplyQueues.objects.filter(event=audio_clip.event).delete()
                AudioClipLikesDislikes.objects.filter(audio_clip=audio_clip).delete()
                AudioClipMetrics.objects.filter(audio_clip=audio_clip).update(like_count=0, dislike_count=0, like_ratio=0)

                #handle event

                if audio_clip.audio_clip_role.audio_clip_role_name == 'originator':

                    #for originator, event always becomes 'deleted'
                    audio_clip.event.generic_status = generic_status_deleted
                    audio_clip.event.save()

                elif (
                    audio_clip.audio_clip_role.audio_clip_role_name == 'responder' and
                    audio_clip.event.generic_status_id == generic_status_completed.id
                ):

                    #for responder, event changes from 'completed' to 'incomplete'
                    audio_clip.event.generic_status = generic_status_incomplete
                    audio_clip.event.save()

                return Response(
                    data={
                        'message': 'Recording has been deleted.',
                    },
                    status=status.HTTP_204_NO_CONTENT
                )

        except AudioClips.DoesNotExist:

            return Response(
                data={
                    'message': get_serializer_error_message(serializer),
                },
                status=status.HTTP_404_NOT_FOUND
            )




































