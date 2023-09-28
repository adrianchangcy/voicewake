from django.http import JsonResponse, QueryDict
from django.db.models import Case, Value, When, Sum, Q, F, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.utils.cache import patch_cache_control
from django.utils.decorators import method_decorator

#auth
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout

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









class EventReportsAPI(generics.GenericAPIView):

    serializer_class = EventReportsAPISerializer
    permission_classes = [IsAuthenticated]

    #no get() here, users don't have to see what events they've reported

    #user wants to report an event
    @method_decorator(app_decorators.deny_if_banned("response"))
    def post(self, request, *args, **kwargs):

        serializer = EventReportsAPISerializer(data=request.data, many=False)

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

            #get event
            target_event = Events.objects.get(pk=new_data['reported_event_id'])

        except Events.DoesNotExist:

            return Response(
                data={
                    'message': 'Recording does not exist.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #check if event belongs to user
        if target_event.user.id == request.user.id:

            return Response(
                data={
                    'message': 'You cannot report your own recording.',
                },
                status=status.HTTP_200_OK
            )

        #check if already banned
        if target_event.is_banned is True:

            return Response(
                data={
                    'message': 'This recording has already been banned.',
                },
                status=status.HTTP_200_OK
            )

        #add report
        EventReports.objects.get_or_create(
            user_id=request.user.id,
            reported_event_id=new_data['reported_event_id']
        )

        return Response(
            data={
                'message': 'We will evaluate the report soon. Thank you for helping to make this a better place.',
            },
            status=status.HTTP_200_OK
        )



class EventBansAPI(generics.GenericAPIView):

    serializer_class = EventsSerializer
    permission_classes = [IsAuthenticated]

    #no post() here, once an event is banned, nobody can do anything
    #cronjob does the banning

    #user wants to see their own banned events
    def get(self, request, *args, **kwargs):

        offset_quantity = 0

        if 'page' in kwargs and kwargs['page'] > 0:

            offset_quantity = settings.GENERAL_ROW_QUANTITY_PER_PAGE * (kwargs['page'] - 1)

        qs = Events.objects.select_related(
            'event__user', 'event__event_tone'
        ).filter(
            event__user=request.user
        ).order_by('-when_created')[
            offset_quantity:settings.GENERAL_ROW_QUANTITY_PER_PAGE
        ]

        banned_events = []

        if len(qs) > 0:

            banned_events = EventsSerializer(
                qs,
                many=True
            ).data

        return Response(
            data={
                'data': banned_events,
                'message': ''
            },
            status=status.HTTP_200_OK
        )



class UserBlocksAPI(generics.GenericAPIView):

    serializer_class = UserBlocksSerializer
    permission_classes = [IsAuthenticated]


    #get list of blocked users
    def get(self, request, *args, **kwargs):

        offset_quantity = 0

        if 'page' in kwargs and kwargs['page'] > 0:

            offset_quantity = settings.GENERAL_ROW_QUANTITY_PER_PAGE * (kwargs['page'] - 1)

        qs = UserBlocks.objects.filter(user=request.user).order_by('-when_created')[
            offset_quantity:settings.GENERAL_ROW_QUANTITY_PER_PAGE
        ]

        serializer = UserBlocksSerializer(
            qs,
            many=True
        )

        return Response(
            data={
                'data': serializer.data,
                'message': ''
            },
            status=status.HTTP_200_OK
        )


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
        blocked_user = get_object_or_404(get_user_model(), pk=new_data['blocked_user_id'])

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
    @method_decorator(app_decorators.deny_if_already_logged_in("response"))
    def post(self, request, *args, **kwargs):

        serializer = UsersLogInAPISerializer(data=request.data, many=False)

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

            user_instance = get_user_model().objects.get(email_lowercase = new_data['email'].lower())

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

                new_otp = handle_user_otp_class.generate_and_save_otp()

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



class EventTonesAPI(generics.GenericAPIView):

    serializer_class = EventTonesSerializer
    permission_classes = []


    def get(self, request, *args, **kwargs):

        response = Response(
            data={
                'message': '',
                'data': EventTonesSerializer(
                    EventTones.objects.all(),
                    many=True
                ).data
            }
        )

        #cache for 4 weeks
        patch_cache_control(
            response,
            no_cache=False, no_store=False, must_revalidate=True, max_age=2419200
        )

        return response



class EventRoomsAPI(generics.GenericAPIView):

    serializer_class = GroupedEventsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


    def get_event_rooms_by_completed(
        self, latest_or_best:Literal['latest', 'best']='latest',
        event_tone_slug:str='',
        timeframe:Literal['day', 'week', 'month', 'all']='all',
        page=1
    ):

        #when event_tone_slug is '', will just get entire event_tones
        #when timeframe is 'all_time', leaving datetime_from as '' is sufficient
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

            #getting earliest events.when_created adds 5-10ms
            #using custom function get_id_of_event_rooms_by_when_created() adds 40ms+

            #random datetime that is guaranteed beyond earliest events row is the best so far
            #here are the risks where this may/would break things:
                #new events.when_created can start using past datetime
                #events.when_created is no longer secured by auto_now_add
                #suddenly no longer uses time zone
            datetime_from = '2020-01-01 01:01:01 +00'

        #calculate offset for pagination
        pagination_offset = (page - 1) * settings.EVENT_ROOM_QUANTITY_PER_PAGE

        #determine order
        order_sql = ''

        if latest_or_best == 'best':
            order_sql = 'ORDER BY events.like_count DESC, events.dislike_count ASC'
        else:
            order_sql = 'ORDER BY events.when_created DESC'

        #start
        events = Events.objects.prefetch_related(
            'event_role',
            'event_room__generic_status',
            'event_room__created_by',
            'event_room',
            'event_tone',
            'generic_status',
            'user',
        ).raw(
            '''		
            WITH
                selected_event_tones AS (
                    SELECT id FROM get_id_of_one_or_all_event_tones_via_slug(%s)
                ),
                event_room_id_of_best_events AS (
                    SELECT DISTINCT event_room_id AS id FROM (
                        SELECT
                            events.event_room_id,
                            events.like_count,
                            events.dislike_count
                        FROM events
                        RIGHT JOIN selected_event_tones ON events.event_tone_id = selected_event_tones.id
                        LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
                        LEFT JOIN event_rooms ON events.event_room_id = event_rooms.id
                        LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
                        LEFT JOIN generic_statuses AS event_rooms_generic_statuses ON event_rooms.generic_status_id = event_rooms_generic_statuses.id
                        WHERE
                        event_rooms_generic_statuses.generic_status_name = %s
                        AND events.when_created BETWEEN %s AND %s
                        GROUP BY events.id
                        ''' + order_sql + '''
                    )
                    AS events_with_count
                    OFFSET %s LIMIT %s
                )
            SELECT
                events.*,
                event_rooms.*,
                event_tones.*,
                generic_statuses.*,
                event_likes_dislikes.is_liked AS is_liked_by_user
            FROM events
            RIGHT JOIN event_room_id_of_best_events ON events.event_room_id = event_room_id_of_best_events.id
            LEFT JOIN event_rooms ON events.event_room_id = event_rooms.id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN event_likes_dislikes ON events.id = event_likes_dislikes.event_id AND event_likes_dislikes.user_id = %s
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            WHERE events.is_banned IS NOT TRUE
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id, is_liked_by_user
            ''',
            params=(
                event_tone_slug,
                'completed',
                datetime_from,
                datetime_to,
                pagination_offset,
                settings.EVENT_ROOM_QUANTITY_PER_PAGE,
                self.request.user.id,
            )
        )

        return events


    def get_event_rooms_by_user_and_event_role(
        self, username:str, event_role_name:str,
        latest_or_best:Literal['latest', 'best']='latest',
        event_tone_slug:str='',
        timeframe:Literal['day', 'week', 'month', 'all']='all',
        page=1
    ):

        #when event_tone_slug is '', will just get entire event_tones
        #when timeframe is 'all_time', leaving datetime_from as '' is sufficient
        #page starts from 1

        if page < 1 or len(username) == 0 or len(event_role_name) == 0:

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

            #getting earliest events.when_created adds 5-10ms
            #using custom function get_id_of_event_rooms_by_when_created() adds 40ms+

            #random datetime that is guaranteed beyond earliest events row is the best so far
            #here are the risks where this may/would break things:
                #new events.when_created can start using past datetime
                #events.when_created is no longer secured by auto_now_add
                #suddenly no longer uses time zone
            datetime_from = '2020-01-01 01:01:01 +00'

        #calculate offset for pagination
        pagination_offset = (page - 1) * settings.EVENT_ROOM_QUANTITY_PER_PAGE

        #determine order
        order_sql = ''

        if latest_or_best == 'best':
            order_sql = 'ORDER BY events.like_count DESC, events.dislike_count ASC'
        else:
            order_sql = 'ORDER BY events.when_created DESC'

        #start
        events = Events.objects.prefetch_related(
            'event_role',
            'event_room__generic_status',
            'event_room__created_by',
            'event_room',
            'event_tone',
            'generic_status',
            'user',
        ).raw(
            '''		
            WITH
                selected_event_tones AS (
                    SELECT id FROM get_id_of_one_or_all_event_tones_via_slug(%s)
                ),
                event_room_id_of_best_events AS (
                    SELECT DISTINCT event_room_id AS id FROM (
                        SELECT
                            events.event_room_id,
                            events.like_count,
                            events.dislike_count
                        FROM events
                        RIGHT JOIN selected_event_tones ON events.event_tone_id = selected_event_tones.id
                        LEFT JOIN voicewake_user ON events.user_id = voicewake_user.id
                        LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
                        LEFT JOIN event_rooms ON events.event_room_id = event_rooms.id
                        LEFT JOIN event_roles ON events.event_role_id = event_roles.id
                        LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
                        LEFT JOIN generic_statuses AS event_rooms_generic_statuses ON event_rooms.generic_status_id = event_rooms_generic_statuses.id
                        WHERE voicewake_user.username_lowercase = %s
                        AND event_roles.event_role_name = %s
                        AND events.when_created BETWEEN %s AND %s
                        GROUP BY events.id
                        ''' + order_sql + '''
                    )
                    AS events_with_count
                    OFFSET %s LIMIT %s
                )
            SELECT
                events.*,
                event_rooms.*,
                event_tones.*,
                generic_statuses.*,
                event_likes_dislikes.is_liked AS is_liked_by_user
            FROM events
            RIGHT JOIN event_room_id_of_best_events ON events.event_room_id = event_room_id_of_best_events.id
            LEFT JOIN event_rooms ON events.event_room_id = event_rooms.id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN event_likes_dislikes ON events.id = event_likes_dislikes.event_id AND event_likes_dislikes.user_id = %s
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id, is_liked_by_user
            ''',
            params=(
                event_tone_slug,
                username.lower(),
                event_role_name,
                datetime_from,
                datetime_to,
                pagination_offset,
                settings.EVENT_ROOM_QUANTITY_PER_PAGE,
                self.request.user.id,
            )
        )

        return events


    def get_event_rooms_by_id(self, event_room_id):

        events = Events.objects.prefetch_related(
            'event_role',
            'event_room__generic_status',
            'event_room__created_by',
            'event_room',
            'event_tone',
            'generic_status',
            'user',
        ).raw(
            '''
            SELECT
                events.*,
                event_rooms.*,
                event_tones.*,
                generic_statuses.*,
                event_likes_dislikes.is_liked AS is_liked_by_user
            FROM events
            LEFT JOIN event_rooms ON events.event_room_id = event_rooms.id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN event_likes_dislikes ON events.id = event_likes_dislikes.event_id AND event_likes_dislikes.user_id = %s
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            WHERE events.event_room_id = %s
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id, is_liked_by_user
            ''',
            params=(
                self.request.user.id,
                event_room_id,
            )
        )

        return events


    #get event_room.id to simply view
    def get(self, request, *args, **kwargs):

        #handle singular event_rooms view
        if 'event_room_id' in kwargs:

            #user simply wants to check the post for an event_room
            response = Response(
                data={
                    'message': '',
                    'data': GroupedEventsSerializer(
                        group_events_into_event_rooms(self.get_event_rooms_by_id(self.kwargs['event_room_id'])),
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
        
        #proceed to handling multiple event_rooms
        
        #pagination
        url_page = 1
        if 'page' in kwargs and kwargs['page'] > 1:
            #URL page starts from 1
            #>1 above allows us to ensure 0 is not used
            url_page = kwargs['page']

        #determine the appropriate results
        response = None

        if(
            'username' in kwargs and 'latest_or_best' in kwargs and
            'timeframe' in kwargs and 'event_role_name' in kwargs and 'page' in kwargs
        ):

            event_tone_slug = ''

            if 'event_tone_slug' in kwargs:
                event_tone_slug = kwargs['event_tone_slug']

            response = Response(
                data={
                    'message': '',
                    'data': GroupedEventsSerializer(
                        group_events_into_event_rooms(
                            self.get_event_rooms_by_user_and_event_role(
                                kwargs['username'],
                                kwargs['event_role_name'],
                                kwargs['latest_or_best'],
                                event_tone_slug,
                                kwargs['timeframe'],
                                url_page,
                            )
                        ),
                        many=True
                    ).data,
                },
                status=status.HTTP_200_OK
            )
        
        elif 'latest_or_best' in kwargs and 'timeframe' in kwargs and 'page' in kwargs:

            url_event_tone_slug = ''
            if 'event_tone_slug' in kwargs:
                url_event_tone_slug = kwargs['event_tone_slug']

            response = Response(
                data={
                    'message': '',
                    'data': GroupedEventsSerializer(
                        group_events_into_event_rooms(
                            self.get_event_rooms_by_completed(
                                kwargs['latest_or_best'],
                                url_event_tone_slug,
                                kwargs['timeframe'],
                                url_page,
                            )
                        ),
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



#user can generate new event_room reply choice
    #will unlock previous is_replying=False event_room
    #will add to UserEventRooms when locking for is_replying=False
class HandleEventRoomReplyChoicesAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = [IsAuthenticated]
    current_context = ""


    def __init__(self, *args, **kwargs):

        if 'current_context' not in kwargs or kwargs['current_context'] not in ['list', 'expire']:

            raise custom_error(ValueError, dev_message="Incorrect current_context passed. Check .as_view() at urls.py.")

        super().__init__(*args, **kwargs)


    def lock_event_rooms_for_reply_choices(self, events):

        User = get_user_model()
        event_room_ids = []
        event_rooms = []
        datetime_now = get_datetime_now()

        for event in events:

            if event.event_room.id not in event_room_ids:

                event_room_ids.append(event.event_room.id)

                #lock for reply choices
                event.event_room.when_locked = datetime_now
                event.event_room.locked_for_user = self.request.user
                event.event_room.is_replying = False
                event.event_room.last_modified = datetime_now

                event_rooms.append(event.event_room)

        EventRooms.objects.bulk_update(event_rooms, ['when_locked', 'locked_for_user', 'is_replying', 'last_modified'])

        #prevent repeated queue
        #we do this here to encourage choosing the best event room, while leaving the other good ones for other users
        prevent_event_room_from_queuing_twice_for_reply(
            self.request.user,
            event_rooms
        )

        return True


    #excludes event_room started by user
    def get_event_rooms_by_random_incomplete(self, event_tone_slug:str=''):

        datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))
        datetime_now = datetime_now.strftime('%Y-%m-%d %H:%M:%S %z')

        #we select only event_rooms.id in selected_event_rooms, followed by event_rooms JOIN
        #because if we do event_rooms.* in selected_event_rooms, we'll have to write all columns in GROUP BY clause
        events = Events.objects.select_for_update(of=("event_room",)).prefetch_related(
            'event_role',
            'event_room__generic_status',
            'event_room__created_by',
            'event_room',
            'event_tone',
            'generic_status',
            'user',
        ).raw(
            '''
            WITH
                selected_event_tones AS (
                    SELECT id FROM get_id_of_one_or_all_event_tones_via_slug(%s)
                ),
                selected_event_rooms AS (
                    SELECT event_rooms.id AS id FROM event_rooms
                    INNER JOIN generic_statuses ON event_rooms.generic_status_id = generic_statuses.id
                    LEFT JOIN user_event_rooms ON event_rooms.id = user_event_rooms.event_room_id AND user_event_rooms.user_id = %s
                    WHERE generic_statuses.generic_status_name = %s
                    AND locked_for_user_id IS NULL
                    AND created_by_id != %s
                    AND user_event_rooms.is_excluded_for_reply IS NOT TRUE
                    ORDER BY event_rooms.when_created DESC
                    LIMIT %s
                )
            SELECT
                events.*,
                selected_event_rooms.*,
                event_tones.*,
                generic_statuses.*,
                event_likes_dislikes.is_liked AS is_liked_by_user
            FROM events
            RIGHT JOIN selected_event_rooms ON events.event_room_id = selected_event_rooms.id
            RIGHT JOIN selected_event_tones ON events.event_tone_id = selected_event_tones.id
            LEFT JOIN event_roles ON events.event_role_id = event_roles.id
            LEFT JOIN event_rooms ON selected_event_rooms.id = event_rooms.id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN event_likes_dislikes ON events.id = event_likes_dislikes.event_id AND event_likes_dislikes.user_id = %s
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            WHERE generic_statuses.generic_status_name = %s
            AND event_roles.event_role_name = %s
            GROUP BY events.id, event_tones.id, generic_statuses.id, selected_event_rooms.id, is_liked_by_user
            ''',
            params=(
                event_tone_slug,
                self.request.user.id,
                'incomplete',
                self.request.user.id,
                settings.EVENT_ROOM_INCOMPLETE_ROLL_QUANTITY,
                self.request.user.id,
                'ok',
                'originator'
            )
        )

        return events


    def unlock_event_rooms_from_past_reply_choices(self):

        User = get_user_model()
        datetime_now = get_datetime_now()

        event_rooms = EventRooms.objects.select_for_update().filter(
            locked_for_user=self.request.user
        )
        
        for event_room in event_rooms:

            #unlock
            event_room.when_locked = None
            event_room.locked_for_user = None
            event_room.is_replying = None
            event_room.last_modified = datetime_now

        EventRooms.objects.bulk_update(event_rooms, ['when_locked', 'locked_for_user', 'is_replying', 'last_modified'])


    def get_event_rooms_by_is_replying(self):

        events = Events.objects.prefetch_related(
            'event_role',
            'event_room__generic_status',
            'event_room__created_by',
            'event_room',
            'event_tone',
            'generic_status',
            'user',
        ).raw(
            '''
            SELECT
                events.*,
                event_rooms.*,
                event_tones.*,
                generic_statuses.*,
                event_likes_dislikes.is_liked AS is_liked_by_user
            FROM events
            LEFT JOIN event_rooms ON events.event_room_id = event_rooms.id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN event_likes_dislikes ON events.id = event_likes_dislikes.event_id AND event_likes_dislikes.user_id = %s
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            LEFT JOIN generic_statuses AS event_rooms_generic_statuses ON event_rooms.generic_status_id = event_rooms_generic_statuses.id
            WHERE event_rooms.locked_for_user_id = %s
            AND event_rooms_generic_statuses.generic_status_name = %s
            AND event_rooms.is_replying = %s
            AND generic_statuses.generic_status_name = %s
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id, is_liked_by_user
            ''',
            params=(
                self.request.user.id,
                self.request.user.id,
                'incomplete',
                True,
                'ok'
            )
        )

        return events


    #queue event room reply choices for user
    @method_decorator([
        app_decorators.deny_if_no_username("response"),
        app_decorators.deny_if_banned("response"),
    ])
    def post(self, request, *args, **kwargs):

        if self.current_context == "list":

            #get possible is_replying
            is_replying_events = self.get_event_rooms_by_is_replying()

            #check if user is replying to anything
            #we want event_room.id if there is any
            if len(is_replying_events) > 0:

                return Response(
                    data={
                        'message': '',
                        'data': GroupedEventsSerializer(
                            group_events_into_event_rooms(is_replying_events),
                            many=True
                        ).data,
                    },
                )
            
        #check if user has specified event_tones
        serializer = HandleEventRoomReplyChoicesAPISerializer(data=request.data, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': 'Invalid data.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_data = serializer.validated_data

        specified_event_tone = None

        try:

            if 'event_tone_id' in new_data:

                specified_event_tone = EventTones.objects.get(pk=new_data['event_tone_id'])

        except EventTones.DoesNotExist:

            return Response(
                data={
                    'message': 'Specified event_tone_id does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:

            with transaction.atomic():

                #user is not replying, continue
                if self.current_context == "list":

                    #not replying, can unlock previous choices if any
                    self.unlock_event_rooms_from_past_reply_choices()

                    #maybe don't unlock on every search
                    #only unlock on skip

                    #get events
                    events = None

                    if specified_event_tone is None:
                        events = self.get_event_rooms_by_random_incomplete()
                    else:
                        events = self.get_event_rooms_by_random_incomplete(event_tone_slug=specified_event_tone.event_tone_slug)

                    if len(events) == 0:

                        return Response(
                            data={
                                'message': '',
                                'data': GroupedEventsSerializer(
                                    [],
                                    many=True
                                ).data,
                            },
                            status=status.HTTP_200_OK
                        )

                    #lock events
                    self.lock_event_rooms_for_reply_choices(events)

                    #return events sorted by event_rooms
                    return Response(
                        data={
                            'message': '',
                            'data': GroupedEventsSerializer(
                                group_events_into_event_rooms(events),
                                many=True
                            ).data,
                        },
                        status=status.HTTP_200_OK
                    )
        
                elif self.current_context == "expire":

                    #has expired, so unlock
                    self.unlock_event_rooms_from_past_reply_choices()

                    return Response(
                        data={
                            'message': 'The event choice has expired. Feel free to search again!'
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



class HandleReplyingEventRoomsAPI(generics.GenericAPIView):

    serializer_class = HandleReplyingEventRoomsAPISerializer
    permission_classes = [IsAuthenticated]
    current_context = ""


    def __init__(self, *args, **kwargs):

        if 'current_context' not in kwargs or kwargs['current_context'] not in ['start', 'cancel']:

            raise custom_error(ValueError, dev_message="Incorrect current_context. Check .as_view() at urls.py.")
    
        super().__init__(*args, **kwargs)


    #if user is already locked for event_room, do is_replying=True and update when_locked
    #for actual replying to start
    #202 success, 205 reset due to user inactivity
    def start_replying_to_event_room(self, event_room_id):

        User = get_user_model()
        datetime_now = get_datetime_now()

        #check if user is replying to any other event_room
        if check_user_is_replying(request=self.request, excluded_event_room_id=event_room_id) is True:

            return Response(
                data={
                    'message': 'You are already replying in a different event.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            with transaction.atomic():

                #get event_room
                #we want to do select_for_update(), but it's not allowed for nullable joins, so we do exclude()
                #also, you must add coma (,) to of=("self",), else it gets unpacked into "s","e","l","f"
                target_event_room = EventRooms.objects.select_related(
                    'generic_status', 'locked_for_user'
                ).select_for_update(
                    of=("self",)
                ).exclude(
                    locked_for_user=None
                ).get(
                    pk=event_room_id
                )

                user = User(self.request.user.id)

                #check if target_event_room is already locked for user beforehand
                #check if target_event_room is not yet expired as a choice
                #check if target_event_room is locked for the correct user
                #if you want to do "extend when_locked", handle target_event_room.is_replying=True
                if\
                    target_event_room.generic_status.generic_status_name == 'incomplete' and\
                    target_event_room.when_locked is not None and\
                    (get_datetime_now() - target_event_room.when_locked).total_seconds() <= settings.EVENT_ROOM_REPLY_CHOICE_EXPIRY_SECONDS and\
                    target_event_room.locked_for_user is not None and target_event_room.locked_for_user.id == self.request.user.id and\
                    target_event_room.is_replying is False\
                :

                    pass

                else:

                    if settings.DEBUG is True:

                        print(target_event_room.generic_status.generic_status_name == 'incomplete')
                        print(target_event_room.when_locked is not None)
                        print((datetime_now - target_event_room.when_locked).total_seconds() <= settings.EVENT_ROOM_REPLY_CHOICE_EXPIRY_SECONDS)
                        print(target_event_room.locked_for_user is not None and target_event_room.locked_for_user.id == self.request.user.id)
                        print(target_event_room.is_replying)

                    raise custom_error(
                        ValueError,
                        user_message="You cannot start replying to this event."
                    )

                #can reply, proceed

                #unlock any other event rooms that were locked for reply choices
                #also save to user_event_rooms to prevent unlocked event_rooms from being queued twice
                event_rooms = EventRooms.objects.filter(
                    locked_for_user=user
                ).select_for_update(
                    of=("self",)
                ).exclude(
                    pk=event_room_id
                )

                for event_room in event_rooms:

                    event_room.when_locked = None
                    event_room.locked_for_user = None
                    event_room.is_replying = None
                    event_room.last_modified = datetime_now

                #unlock
                EventRooms.objects.bulk_update(event_rooms, ['when_locked', 'locked_for_user', 'is_replying', 'last_modified'])

                #confirm reply, start over when_locked
                target_event_room.when_locked = get_datetime_now()
                target_event_room.is_replying = True
                target_event_room.save()

                return Response(
                    data={
                        'message': 'Success! You are now replying to this event.',
                    },
                    status=status.HTTP_202_ACCEPTED
                )
            
        except EventRooms.DoesNotExist:

            return Response(
                data={
                    'message': 'This event no longer exists.',
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
    #204 nothing to cancel, 205 success
    def cancel_replying_to_event_room(self, event_room_id):

        try:

            with transaction.atomic():

                #get event_room
                event_room = EventRooms.objects.select_related(
                    'generic_status', 'locked_for_user'
                ).select_for_update(
                    of=("self",)
                ).get(
                    pk=event_room_id
                )

                #check if user is already replying
                #we don't check for time limit, as cancellation can occur beyond it
                if\
                    event_room.when_locked is not None and\
                    event_room.is_replying is True and\
                    event_room.locked_for_user is not None and event_room.locked_for_user.id == self.request.user.id\
                :

                    pass

                else:

                    #under these conditions, we want to allow cancellation without error
                    #UI being removed is of higher priority than status_code
                    return Response(
                        data={
                            'message': 'Cannot cancel this replying process.',
                        },
                        status=status.HTTP_204_NO_CONTENT
                    )

                #cancel replying
                event_room.locked_for_user = None
                event_room.is_replying = None
                event_room.when_locked = None

                #careful not to change 'deleted' to 'incomplete'
                if event_room.generic_status.generic_status_name != 'deleted':

                    event_room.generic_status = GenericStatuses.objects.get(generic_status_name='incomplete')

                event_room.save()

                return Response(
                    data={
                        'message': 'Reply has been cancelled.',
                    },
                    status=status.HTTP_205_RESET_CONTENT
                )
            
        except EventRooms.DoesNotExist:

            return Response(
                data={
                    'message': 'This event no longer exists.',
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

        serializer = HandleReplyingEventRoomsAPISerializer(data=request.data, many=False)

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

            return self.start_replying_to_event_room(new_data['event_room_id'])
        
        elif self.current_context == "cancel":

            return self.cancel_replying_to_event_room(new_data['event_room_id'])



#does not have own get(), since viewing events always involves parent event_rooms
#handle creating events
    #if event_role_name='originator', create event_room
    #if event_role_name='responder', link to event_room and reset lock
class EventsAPI(generics.GenericAPIView):

    serializer_class = CreateEventsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = None
    current_context = ""


    def __init__(self, *args, **kwargs):

        if 'current_context' not in kwargs or kwargs['current_context'] not in ['create_new', 'reply']:

            raise custom_error(ValueError, dev_message="Incorrect current_context passed. Check .as_view() at urls.py.")
    
        super().__init__(*args, **kwargs)


    def check_user_create_event_room_daily_limit(self, user):

        #this is for "X max new event rooms every __", which in this case is every 24h
        datetime_checkpoint = datetime.now().astimezone(tz=ZoneInfo('UTC')).strftime('%Y-%m-%d 00:00:00 %z')
        datetime_checkpoint = datetime.strptime(datetime_checkpoint, '%Y-%m-%d %H:%M:%S %z')

        the_count = EventRooms.objects.filter(
            created_by=user,
            when_created__gte=datetime_checkpoint
        ).count()

        if the_count < settings.EVENT_ROOM_CREATE_DAILY_LIMIT:

            return False

        return True


    def check_user_create_reply_event_daily_limit(self, user):

        #this is for "X max new posts every __", which in this case is every 24h
        datetime_checkpoint = datetime.now().astimezone(tz=ZoneInfo('UTC')).strftime('%Y-%m-%d 00:00:00 %z')
        datetime_checkpoint = datetime.strptime(datetime_checkpoint, '%Y-%m-%d %H:%M:%S %z')

        the_count = Events.objects.filter(
            user=user,
            when_created__gte=datetime_checkpoint
        ).count()

        if the_count < settings.EVENT_ROOM_REPLY_DAILY_LIMIT:

            return False

        return True


    def check_user_can_reply_event_room(self, event_room):

        #check if user is replying
        if\
            event_room.locked_for_user is not None and\
            event_room.locked_for_user.id == self.request.user.id and\
            event_room.is_replying is True\
        :

            return True

        return False


    def check_user_exceeded_reply_time_window(self, event_room):

        minutes_passed = (get_datetime_now() - event_room.when_locked).total_seconds()

        if minutes_passed > settings.EVENT_ROOM_REPLY_CHOICE_EXPIRY_SECONDS:

            return True
        
        return False


    @method_decorator([
        app_decorators.deny_if_no_username("response"),
        app_decorators.deny_if_banned("response"),
    ])
    def post(self, request, *args, **kwargs):

        #deserialize
        serializer = CreateEventsSerializer(data=request.data, many=False)

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

                #event_tone
                event_tone = EventTones.objects.get(pk=new_data['event_tone_id'])

                #determine if originator/responder, then create/get event_room
                #generic_status is handled by default, so it is skipped here
                if self.current_context == "create_new":

                    #check if created event_room limit is not yet reached
                    if self.check_user_create_event_room_daily_limit(request.user) is True:

                        raise custom_error(
                            TimeoutError,
                            user_message="You have reached your daily limit for creating events."
                        )

                    #proceed
                    event_role = EventRoles.objects.get(event_role_name='originator')

                    event_room = EventRooms.objects.create(
                        event_room_name=new_data['event_room_name'],
                        generic_status=GenericStatuses.objects.get(generic_status_name='incomplete'),
                        created_by=request.user
                    )

                elif self.current_context == "reply":

                    #check if reply event limit is not yet reached
                    if self.check_user_create_reply_event_daily_limit(request.user) is True:

                        raise custom_error(
                            ValueError,
                            user_message="You have reached your daily limit of replies."
                        )

                    #get event_room
                    event_room = EventRooms.objects.select_for_update().get(pk=new_data['event_room_id'])

                    #check if this user is already attached beforehand
                    if self.check_user_can_reply_event_room(event_room) is False:

                        raise custom_error(
                            ValueError,
                            user_message="Replying to this event is not allowed."
                        )
                    
                    #check if user exceeded reply time window but automated script has not detected yet
                    if self.check_user_exceeded_reply_time_window(event_room) is True:

                        #reset
                        event_room.locked_for_user = None
                        event_room.when_locked = None
                        event_room.is_replying = None
                        event_room.save()

                        raise custom_error(
                            TimeoutError,
                            user_message="Reply was not successful. You had reached the time limit."
                        )

                    #mark event_room as completed, remove lock
                    event_room.generic_status = GenericStatuses.objects.get(generic_status_name='completed')
                    event_room.when_locked = None
                    event_room.locked_for_user = None
                    event_room.is_replying = None
                    event_room.save()

                    #can proceed
                    event_role = EventRoles.objects.get(event_role_name='responder')
                
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

                #create event, excluding audio_file and event_room
                #generic_status is handled by default, so it is skipped here
                new_event = Events.objects.create(
                    user=request.user,
                    event_role=event_role,
                    event_tone=event_tone,
                    event_room=event_room,
                    audio_volume_peaks=handle_audio_file_class.peak_buckets,
                    audio_duration_s=handle_audio_file_class.audio_file_duration_s
                )

                #we delay saving audio_file, as we want when_created for audio_file's path
                new_event.audio_file = handle_audio_file_class.audio_file
                new_event.save()

                #close just in case it's no longer a reference, i.e. Django won't auto-close
                handle_audio_file_class.close_audio_file()

                return Response(
                    {
                        'data': {
                            'event_room_id': event_room.id
                        },
                        'message': 'Success!',
                    },
                    status.HTTP_201_CREATED
                )
        
        except EventTones.DoesNotExist:

            return Response(
                data={
                    'message': 'Your selected tag was not found. Try a different one.',
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        except EventRooms.DoesNotExist:

            return Response(
                data={
                    'message': 'This event no longer exists.',
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
class EventLikesDislikesAPI(generics.GenericAPIView):

    serializer_class = EventLikesDislikesSerializer
    permission_classes = [IsAuthenticated]

    #no get() needed, since likes/dislikes are tied directly to events

    #create
    @method_decorator([
        app_decorators.deny_if_no_username("response"),
        app_decorators.deny_if_banned("response"),
    ])
    def post(self, request, *args, **kwargs):

        User = get_user_model()

        serializer = CreateEventLikesDislikesSerializer(data=request.data, many=False)

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

        #check if event exists
        if Events.objects.filter(pk=new_data['event_id']).exists() is False:

            return Response(
                data={
                    'message': 'Event no longer exists.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        #these solutions didn't help prevent race condition
            #direct .filter().update(like_count=F('like_count') + 1)
            #like_count = F('like_count) + 1; .save()
        #what worked:
            #using trigger that also checks for OLD.is_liked != NEW.is_liked during INSERT prevents race condition
        #peculiar:
            #with/without trigger, both yield the same response times (avg. 17000ms)

        #start

        try:

            if new_data['is_liked'] is None:

                #this is safe from "performing deletion but no rows found"
                EventLikesDislikes.objects.filter(
                    user_id=request.user.id,
                    event_id=new_data['event_id']
                ).delete()

            else:

                #for value changes, use defaults arg
                EventLikesDislikes.objects.update_or_create(
                    user_id=request.user.id,
                    event_id=new_data['event_id'],
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
                        'message': 'Unable to like/dislike this event.',
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except:

            traceback.print_exc()

            return Response(
                data={
                    'message': 'Unable to like/dislike this event.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            data={
                'message': '',
            },
            status=status.HTTP_200_OK
        )




























