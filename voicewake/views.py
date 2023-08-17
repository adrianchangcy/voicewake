from django.http import JsonResponse, QueryDict
from django.db.models import Case, Value, When, Sum, Q, F, Count
from django.shortcuts import render, redirect
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import get_template
from django.utils.cache import patch_cache_control

#auth
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, permission_required

#DRF, class-based views
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework import viewsets, generics
    #ModelViewSet has: list, create, retrieve, update, partial_update, destroy
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

#Django views
from django.views.generic.list import ListView
from django.views.generic import TemplateView

#mixins
from django.contrib.auth.mixins import PermissionRequiredMixin

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
from voicewake.forms import *
from voicewake.models import *
from voicewake.serializers import *
from voicewake.services import *
from django.conf import settings



#===direct web pages===
# @login_required(login_url='/login')
def home(request):

    return render(request, template_name='voicewake/home.html')


def log_in(request):

    return render(request, template_name='registration/log_in.html')


def sign_up(request):

    return render(request, template_name='registration/sign_up.html')

#======================


class UsersUsernameAPI(generics.GenericAPIView):

    serializer_class = UsersUsernameAPISerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    #checks if username exists
    def get(self, request, *args, **kwargs):

        serializer = UsersUsernameAPISerializer(data=kwargs, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': 'Invalid data.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_data = serializer.validated_data

        User = get_user_model()
        
        exists = User.objects.filter(
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
    def post(self, request, *args, **kwargs):

        User = get_user_model()

        user_instance = User.objects.get(pk=request.user.id)

        #user must not already have a username
        if user_instance.username is not None:

            return Response(
                {
                    'message': 'You already have a username.',
                },
                status.HTTP_403_FORBIDDEN
            )

        #validate
        serializer = UsersUsernameAPISerializer(data=request.data, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': 'Invalid data.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        #check again if it exists
        username_exists = User.objects.filter(
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
        user_instance.username = new_data['username']
        user_instance.username_lowercase = new_data['username'].lower()
        user_instance.save()

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



class UsersLogInAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = []


    def verify_and_log_in(self, request, user_instance, handle_user_otp_class:HandleUserOTP, otp):

        #reminder that verify_otp() does all the checks for us
        if handle_user_otp_class.verify_otp(otp) is False:

            #do not let users know about max attempts reached
            #this protects against email probing during login

            return HandleUserOTP.get_default_verify_otp_response()

        #OTP verified, continue

        #currently set to True because we have no implication for is_active=False
        if user_instance.is_active is False:

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


    def post(self, request, *args, **kwargs):

        serializer = UsersLogInAPISerializer(data=request.data, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': 'Invalid data.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data
        User = get_user_model()
        user_instance = None

        #get user
        #reminder that user shall always exist if following through account creation
        try:

            user_instance = User.objects.get(email_lowercase = new_data['email'].lower())

        except User.DoesNotExist:

            #we do this to obscure clues that a user may or may not exist
            if new_data['is_requesting_new_otp'] is True:

                #no need to notify non-registered emails on login attempts
                #prevents the attack where our website is used as the source of DDOS (towards Gmail in this case)

                #fake delay
                #during testing, send_mail() takes quite long, around 2+ secs
                time.sleep(random.uniform(0.8, 2))

                return HandleUserOTP.get_default_create_otp_response(email=new_data['email'])
            
            return HandleUserOTP.get_default_verify_otp_response()
        
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

                    handle_user_otp_class.send_otp_email(
                        new_data['email'],
                        'Code for login',
                        'Log in with this code:',
                        new_otp
                    )

                return HandleUserOTP.get_default_create_otp_response(new_data['email'])

            #continue to verifying OTP and logging in
            #will always return Response()
            return self.verify_and_log_in(request, user_instance, handle_user_otp_class, new_data['otp'])



class UsersSignUpAPI(UsersLogInAPI):

    serializer_class = None
    permission_classes = []


    def post(self, request, *args, **kwargs):

        #same data as signing in
        serializer = UsersLogInAPISerializer(data=request.data, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': 'Invalid data.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data
        User = get_user_model()
        user_instance = None
        email_lowercase = new_data['email'].lower()

        try:

            #get user
            user_instance = User.objects.get(
                email_lowercase=email_lowercase
            )

        except User.DoesNotExist:

            #create user
            user_instance = User.objects.create_user(
                email=new_data['email'],
            )

        with transaction.atomic():

            #start with OTP
            handle_user_otp_class = HandleUserOTP(
                user_instance, settings.TOTP_NUMBER_OF_DIGITS, settings.TOTP_VALIDITY_SECONDS, settings.TOTP_TOLERANCE_SECONDS,
                settings.OTP_CREATE_TIMEOUT_SECONDS, settings.OTP_MAX_ATTEMPTS, settings.OTP_MAX_ATTEMPT_TIMEOUT_SECONDS
            )
            handle_user_otp_class.get_or_create_user_otp_instance()
            
            #handle request for new OTP
            if new_data['is_requesting_new_otp'] is True:
            
                new_otp = handle_user_otp_class.generate_and_save_otp()
    
                #only send email if has legitimate new OTP
                if len(new_otp) == settings.TOTP_NUMBER_OF_DIGITS:
                
                    handle_user_otp_class.send_otp_email(
                        new_data['email'],
                        'Code for sign-up',
                        'Complete your sign-up with this code:',
                        new_otp
                    )
    
                return HandleUserOTP.get_default_create_otp_response(new_data['email'])
    
            #continue to verifying OTP and logging in
            #will always return Response()
            return self.verify_and_log_in(request, user_instance, handle_user_otp_class, new_data['otp'])



class UsersLogOutAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = []


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









#=====REST APIs=====

class EventTonesAPI(viewsets.ReadOnlyModelViewSet):

    serializer_class = EventTonesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = EventTones.objects.all()


    def get_queryset(self):

        search = self.request.query_params.get('search')

        if search is not None:

            #part of search optimisation is "... field_name LIKE 'string%' OR field_name LIKE '%string%'"
            #Q is used to encapsulate a collection of keyword arguments
            return EventTones.objects.filter(
                Q(event_tone_name__istartswith=search)|Q(event_tone_name__icontains=search)
            )[:10]
            
        else:
        
            return EventTones.objects.all()



class EventRoomsAPI(generics.GenericAPIView):

    serializer_class = EventRoomsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


    def get_queryset_all_test(self):

        events = Events.objects.raw(
            '''
            SELECT
                events.*,
                event_rooms.*,
                event_tones.*,
                generic_statuses.*,
                SUM(
                    CASE 
                    WHEN event_likes_dislikes.is_liked='true' AND event_likes_dislikes.event_id IN (events.id) THEN 1
                    ELSE 0
                    END
                ) AS like_count,
                SUM(
                    CASE
                    WHEN event_likes_dislikes.is_liked='false' AND event_likes_dislikes.event_id IN (events.id) THEN 1
                    ELSE 0
                    END
                ) AS dislike_count,
                (CASE
                    (
                        SELECT event_likes_dislikes.is_liked
                        FROM event_likes_dislikes
                        WHERE user_id=%s
                        AND event_id=events.id
                    )
                    WHEN 'true' THEN 'true'
                    WHEN 'false' THEN 'false'
                    ELSE NULL
                    END
                ) as is_liked_by_user
            FROM events
            LEFT JOIN event_rooms ON events.event_room_id = event_rooms.id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN event_likes_dislikes ON  events.id = event_likes_dislikes.event_id
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id
            ''',
            params=(
                self.request.user.id,
            )
        )
        return events


    def get_queryset_by_is_replying(self):

        events = Events.objects.raw(
            '''
            SELECT
                events.*,
                event_rooms.*,
                event_tones.*,
                generic_statuses.*,
                SUM(
                    CASE 
                    WHEN event_likes_dislikes.is_liked='true' AND event_likes_dislikes.event_id IN (events.id) THEN 1
                    ELSE 0
                    END
                ) AS like_count,
                SUM(
                    CASE
                    WHEN event_likes_dislikes.is_liked='false' AND event_likes_dislikes.event_id IN (events.id) THEN 1
                    ELSE 0
                    END
                ) AS dislike_count,
                (CASE
                    (
                        SELECT event_likes_dislikes.is_liked
                        FROM event_likes_dislikes
                        WHERE user_id=%s
                        AND event_id=events.id
                    )
                    WHEN 'true' THEN 'true'
                    WHEN 'false' THEN 'false'
                    ELSE NULL
                    END
                ) as is_liked_by_user
            FROM events
            LEFT JOIN event_rooms ON events.event_room_id = event_rooms.id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN event_likes_dislikes ON  events.id = event_likes_dislikes.event_id
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            WHERE events.event_room_id IN (
                SELECT id FROM event_rooms
                WHERE locked_for_user_id=%s
                AND is_replying=%s
            )
            AND generic_statuses.generic_status_name = %s
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id
            ''',
            params=(
                self.request.user.id,
                self.request.user.id,
                True,
                'ok'
            )
        )

        return events


    def get_queryset_by_best_completed(self):

        #this is for "10 max new posts every >= __", which in this case is every hour
        checkpoint_datetime = datetime.now().astimezone(tz=ZoneInfo('UTC')).strftime('%Y-%m-%d %H:00:00 %z')
        checkpoint_datetime = datetime.strptime(checkpoint_datetime, '%Y-%m-%d %H:%M:%S %z')

        events = Events.objects.raw(
            '''
            SELECT
                events.*,
                event_rooms.*,
                event_tones.*,
                generic_statuses.*,
                SUM(
                    CASE 
                    WHEN event_likes_dislikes.is_liked='true' AND event_likes_dislikes.event_id IN (events.id) THEN 1
                    ELSE 0
                    END
                ) AS like_count,
                SUM(
                    CASE
                    WHEN event_likes_dislikes.is_liked='false' AND event_likes_dislikes.event_id IN (events.id) THEN 1
                    ELSE 0
                    END
                ) AS dislike_count,
                (CASE
                    (
                        SELECT event_likes_dislikes.is_liked
                        FROM event_likes_dislikes
                        WHERE user_id=%s
                        AND event_id=events.id
                    )
                    WHEN 'true' THEN 'true'
                    WHEN 'false' THEN 'false'
                    ELSE NULL
                    END
                ) as is_liked_by_user
            FROM events
            LEFT JOIN event_rooms ON events.event_room_id = event_rooms.id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN event_likes_dislikes ON  events.id = event_likes_dislikes.event_id
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            WHERE events.event_room_id IN (
                SELECT event_rooms.id FROM event_rooms
                INNER JOIN generic_statuses ON event_rooms.generic_status_id = generic_statuses.id
                WHERE generic_statuses.generic_status_name=%s
                AND event_rooms.when_created >= %s
                LIMIT %s
            )
            AND generic_statuses.generic_status_name = %s
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id
            ORDER BY like_count DESC
            ''',
            params=(
                self.request.user.id,
                'completed',
                checkpoint_datetime,
                SPECIAL_EVENT_ROOMS_QUANTITY,
                'ok'
            )
        )

        return events


    def get_queryset_by_event_room(self):

        events = Events.objects.raw(
            '''
            SELECT
                events.*,
                event_rooms.*,
                event_tones.*,
                generic_statuses.*,
                SUM(
                    CASE 
                    WHEN event_likes_dislikes.is_liked='true' AND event_likes_dislikes.event_id IN (events.id) THEN 1
                    ELSE 0
                    END
                ) AS like_count,
                SUM(
                    CASE
                    WHEN event_likes_dislikes.is_liked='false' AND event_likes_dislikes.event_id IN (events.id) THEN 1
                    ELSE 0
                    END
                ) AS dislike_count,
                (CASE
                    (
                        SELECT event_likes_dislikes.is_liked
                        FROM event_likes_dislikes
                        WHERE user_id=%s
                        AND event_id=events.id
                    )
                    WHEN 'true' THEN 'true'
                    WHEN 'false' THEN 'false'
                    ELSE NULL
                    END
                ) as is_liked_by_user
            FROM events
            LEFT JOIN event_rooms ON events.event_room_id = event_rooms.id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN event_likes_dislikes ON  events.id = event_likes_dislikes.event_id
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            WHERE events.event_room_id = %s
            AND generic_statuses.generic_status_name = %s
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id
            ''',
            params=(
                self.request.user.id,
                self.kwargs['event_room_id'],
                'ok'
            )
        )

        return events


    #get event_room.id to simply view
    #or get by generic_status_name='incomplete' to lock events as reply choices
        #will give currently replying event_room, or unlock reply choices and lock new ones
    def get(self, request, *args, **kwargs):

        #handle singular event_room view
        if 'event_room_id' in kwargs:

            #user simply wants to check the post for an event_room
            response = Response(
                data={
                    'message': '',
                    'data': EventRoomsSerializer(
                        sort_events_into_event_rooms(self.get_queryset_by_event_room()),
                        many=True
                    ).data,
                },
            )

            #if user is replying, we don't cache the request
            #in regards to replying UI not disappearing when user revisits
            if check_user_is_replying(request) is True:

                patch_cache_control(
                    response,
                    no_cache=True, no_store=True, must_revalidate=True, max_age=0
                )

            return response
        
        #not singular event_room, so return many
        #TODO: pagination?



#does not have own get(), since viewing events always involves parent event_rooms
#handle creating events
    #if event_role_name='originator', create event_room
    #if event_role_name='responder', link to event_room and reset lock
class EventsAPI(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = EventsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = None
    user_action:Literal["create_new", "reply"] = ""


    def check_user_create_event_room_daily_limit(self, user):

        #this is for "X max new event rooms every __", which in this case is every 24h
        checkpoint_datetime = datetime.now().astimezone(tz=ZoneInfo('UTC')).strftime('%Y-%m-%d 00:00:00 %z')
        checkpoint_datetime = datetime.strptime(checkpoint_datetime, '%Y-%m-%d %H:%M:%S %z')

        the_count = EventRooms.objects.filter(
            created_by=user,
            when_created__gte=checkpoint_datetime
        ).count()

        if the_count < settings.EVENT_ROOM_CREATE_DAILY_LIMIT:

            return False

        return True


    def check_user_create_reply_event_daily_limit(self, user):

        #this is for "X max new posts every __", which in this case is every 24h
        checkpoint_datetime = datetime.now().astimezone(tz=ZoneInfo('UTC')).strftime('%Y-%m-%d 00:00:00 %z')
        checkpoint_datetime = datetime.strptime(checkpoint_datetime, '%Y-%m-%d %H:%M:%S %z')

        the_count = Events.objects.filter(
            user=user,
            when_created__gte=checkpoint_datetime
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


    def post(self, request, *args, **kwargs):

        User = get_user_model()

        #deserialize
        serializer = CreateEventsSerializer(data=request.data, many=False)

        #validate overall
        if serializer.is_valid() is False and len(serializer.errors) > 0:

            #return any first error message
            for key in serializer.errors:
                for first_error in serializer.errors[key]:
                    return Response(
                        data={
                            'message': first_error,
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

        #ok, continue
        new_data = serializer.validated_data
        user = User(pk=request.user.id)

        try:

            with transaction.atomic():

                #event_tone
                event_tone = EventTones.objects.get(pk=new_data['event_tone_id'])

                #determine if originator/responder, then create/get event_room
                #generic_status is handled by default, so it is skipped here
                if self.user_action == "create_new":

                    #check if created event_room limit is not yet reached
                    if self.check_user_create_event_room_daily_limit(user) is True:

                        raise HandleError.new_error(
                            TimeoutError,
                            user_message="You have reached your daily limit for creating events."
                        )

                    #proceed
                    event_role = EventRoles.objects.get(event_role_name='originator')

                    event_room = EventRooms.objects.create(
                        event_room_name=new_data['event_room_name'],
                        generic_status=GenericStatuses.objects.get(generic_status_name='incomplete'),
                        created_by=user
                    )

                elif self.user_action == "reply":

                    #check if reply event limit is not yet reached
                    if self.check_user_create_reply_event_daily_limit(user) is True:

                        raise HandleError.new_error(
                            ValueError,
                            user_message="You have reached your daily limit of replies."
                        )

                    #get event_room
                    event_room = EventRooms.objects.select_for_update().get(pk=new_data['event_room_id'])

                    #check if this user is already attached beforehand
                    if self.check_user_can_reply_event_room(event_room) is False:

                        raise HandleError.new_error(
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

                        #prevent from being queued twice
                        prevent_event_room_from_queuing_twice_for_reply(user, event_room)

                        raise HandleError.new_error(
                            TimeoutError,
                            user_message="Reply was not successful. You had reached the time limit."
                        )

                    #mark event_room as completed, remove lock
                    event_room.generic_status = GenericStatuses.objects.get(generic_status_name='completed')
                    event_room.when_locked = None
                    event_room.locked_for_user = None
                    event_room.is_replying = None
                    event_room.save()

                    #proceed
                    event_role = EventRoles.objects.get(event_role_name='responder')

                else:

                    raise HandleError.new_error(
                        AttributeError,
                        dev_message="Unrecognised user_action arg from urls.py."
                    )
                
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
                    user=user,
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
                    'message': HandleError.get_user_message(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except ValueError as e:

            return Response(
                data={
                    'message': HandleError.get_user_message(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:

            traceback.print_exc()

            print(HandleError.get_dev_message(e))

            return Response(
                data={
                    'message': HandleError.get_user_message(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )





















#TODO: wrap in transaction.atomic() and clarify try-except for everything
#TODO: implement try-except MySerializer.ValidationError for everything
#TODO: do prevent_event_room_from_queuing_twice_for_reply() better
#user can generate new event_room reply choice
    #will unlock previous is_replying=False event_room
    #will add to UserEventRooms when locking for is_replying=False
class HandleEventRoomReplyChoicesAPI(generics.GenericAPIView):

    serializer_class = None
    permission_classes = [IsAuthenticated]
    user_context:Literal["list", "expire"] = ""


    def lock_event_rooms_for_reply_choices(self, events):

        User = get_user_model()
        event_room_ids = []
        datetime_now = get_datetime_now()

        for event in events:

            if event.event_room.id not in event_room_ids:

                event_room_ids.append(event.event_room.id)

                #lock for reply choices
                event.event_room.when_locked = datetime_now
                event.event_room.locked_for_user = User(pk=self.request.user.id)
                event.event_room.is_replying = False
                event.event_room.save()

                #prevent repeated queue
                prevent_event_room_from_queuing_twice_for_reply(
                    User(pk=self.request.user.id),
                    event.event_room
                )

        return True


    #excludes event_room started by user
    def get_queryset_by_random_incomplete(self):

        events = Events.objects.select_for_update(of=("event_rooms",)).raw(
            '''
            SELECT
                events.*,
                event_rooms.*,
                event_tones.*,
                generic_statuses.*,
                SUM(
                    CASE 
                    WHEN event_likes_dislikes.is_liked='true' AND event_likes_dislikes.event_id IN (events.id) THEN 1
                    ELSE 0
                    END
                ) AS like_count,
                SUM(
                    CASE
                    WHEN event_likes_dislikes.is_liked='false' AND event_likes_dislikes.event_id IN (events.id) THEN 1
                    ELSE 0
                    END
                ) AS dislike_count,
                (CASE
                    (
                        SELECT event_likes_dislikes.is_liked
                        FROM event_likes_dislikes
                        WHERE user_id=%s
                        AND event_id=events.id
                    )
                    WHEN 'true' THEN 'true'
                    WHEN 'false' THEN 'false'
                    ELSE NULL
                    END
                ) as is_liked_by_user
            FROM events
            LEFT JOIN event_rooms ON events.event_room_id = event_rooms.id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN event_likes_dislikes ON  events.id = event_likes_dislikes.event_id
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            WHERE
            events.event_room_id IN (
                SELECT event_rooms.id FROM event_rooms
                INNER JOIN generic_statuses ON event_rooms.generic_status_id = generic_statuses.id
                WHERE generic_statuses.generic_status_name=%s
                AND locked_for_user_id IS NULL
                AND created_by_id != %s
                ORDER BY event_rooms.when_created ASC
            )
            AND events.event_room_id NOT IN (
                SELECT user_event_rooms.event_room_id FROM user_event_rooms
                INNER JOIN event_rooms ON user_event_rooms.event_room_id = event_rooms.id
                WHERE user_id=%s
                AND is_excluded_for_reply IS TRUE
            )
            AND events.event_room_id NOT IN (
                SELECT events2.event_room_id FROM events AS events2
                WHERE user_id=%s
            )
            AND generic_statuses.generic_status_name = %s
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id
            LIMIT %s
            ''',
            params=(
                self.request.user.id,
                'incomplete',
                self.request.user.id,
                self.request.user.id,
                self.request.user.id,
                'ok',
                INCOMPLETE_EVENT_ROOMS_PER_ROLL,
            )
        )

        return events


    def unlock_event_rooms_from_past_reply_choices(self):

        User = get_user_model()

        event_rooms = EventRooms.objects.select_for_update().filter(
            locked_for_user=User(pk=self.request.user.id)
        )
        
        user = User(pk=self.request.user.id)

        for event_room in event_rooms:

            #unlock
            event_room.when_locked = None
            event_room.locked_for_user = None
            event_room.is_replying = None

            event_room.save()


    def get_queryset_by_is_replying(self):

        events = Events.objects.raw(
            '''
            SELECT
                events.*,
                event_rooms.*,
                event_tones.*,
                generic_statuses.*,
                SUM(
                    CASE 
                    WHEN event_likes_dislikes.is_liked='true' AND event_likes_dislikes.event_id IN (events.id) THEN 1
                    ELSE 0
                    END
                ) AS like_count,
                SUM(
                    CASE
                    WHEN event_likes_dislikes.is_liked='false' AND event_likes_dislikes.event_id IN (events.id) THEN 1
                    ELSE 0
                    END
                ) AS dislike_count,
                (CASE
                    (
                        SELECT event_likes_dislikes.is_liked
                        FROM event_likes_dislikes
                        WHERE user_id=%s
                        AND event_id=events.id
                    )
                    WHEN 'true' THEN 'true'
                    WHEN 'false' THEN 'false'
                    ELSE NULL
                    END
                ) as is_liked_by_user
            FROM events
            LEFT JOIN event_rooms ON events.event_room_id = event_rooms.id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN event_likes_dislikes ON  events.id = event_likes_dislikes.event_id
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            WHERE events.event_room_id IN (
                SELECT id FROM event_rooms
                WHERE locked_for_user_id=%s
                AND is_replying=%s
            )
            AND generic_statuses.generic_status_name = %s
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id
            ''',
            params=(
                self.request.user.id,
                self.request.user.id,
                True,
                'ok'
            )
        )

        return events


    #queue event room reply choices for user
    def post(self, request, *args, **kwargs):

        if self.user_context == "list":

            #get possible is_replying
            is_replying_events = self.get_queryset_by_is_replying()

            #check if user is replying to anything
            #we want event_room.id if there is any
            if len(is_replying_events) > 0:

                return Response(
                    data={
                        'message': '',
                        'data': EventRoomsSerializer(
                            sort_events_into_event_rooms(is_replying_events),
                            many=True
                        ).data,
                    },
                )
        
        try:

            with transaction.atomic():

                #user is not replying, continue
                if self.user_context == "list":

                    #not replying, can unlock previous choices if any
                    self.unlock_event_rooms_from_past_reply_choices()

                    #get events
                    events = self.get_queryset_by_random_incomplete()

                    if len(events) == 0:

                        return Response(
                            data={
                                'message': '',
                                'data': EventRoomsSerializer(
                                    [],
                                    many=True
                                ).data,
                            },
                        )

                    #lock events
                    #also calls prevent_event_room_from_queuing_twice_for_reply()
                    self.lock_event_rooms_for_reply_choices(events)

                    #return events sorted by event_rooms
                    return Response(
                        data={
                            'message': '',
                            'data': EventRoomsSerializer(
                                sort_events_into_event_rooms(events),
                                many=True
                            ).data,
                        },
                    )
        
                elif self.user_context == "expire":

                    #has expired, so unlock
                    self.unlock_event_rooms_from_past_reply_choices()

                    return Response(
                        data={
                            'message': 'The event choice has expired for being unselected for too long. Feel free to search again!'
                        },
                        status=status.HTTP_205_RESET_CONTENT
                    )

                else:

                    raise HandleError.new_error(
                        AttributeError,
                        dev_message="Invalid user_context arg from urls.py."
                    )
                
        except Exception as e:

            return Response(
                data={
                    'message': HandleError.get_user_message(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )



class HandleReplyingEventRoomsAPI(generics.GenericAPIView):

    serializer_class = HandleReplyingEventRoomsSerializer
    permission_classes = [IsAuthenticated]
    user_action:Literal["start", "cancel"] = ""


    #if user is already locked for event_room, do is_replying=True and update when_locked
    #for actual replying to start
    #202 success, 205 reset due to user inactivity
    def start_replying_to_event_room(self, event_room_id):

        User = get_user_model()

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
                event_room = EventRooms.objects.select_related(
                    'generic_status', 'locked_for_user'
                ).select_for_update(
                    of=("self",)
                ).exclude(
                    locked_for_user=None
                ).get(
                    pk=event_room_id
                )

                user = User(self.request.user.id)

                #check if event_room is already locked for user beforehand
                #check if event_room is not yet expired as a choice
                #check if event_room is locked for the correct user
                #if you want to do "extend when_locked", handle event_room.is_replying=True
                if\
                    event_room.generic_status.generic_status_name == 'incomplete' and\
                    event_room.when_locked is not None and\
                    (get_datetime_now() - event_room.when_locked).total_seconds() <= settings.EVENT_ROOM_REPLY_CHOICE_EXPIRY_SECONDS and\
                    event_room.locked_for_user is not None and event_room.locked_for_user.id == self.request.user.id and\
                    event_room.is_replying is False\
                :

                    pass

                else:

                    if settings.DEBUG is True:

                        print(event_room.generic_status.generic_status_name == 'incomplete')
                        print(event_room.when_locked is not None)
                        print((get_datetime_now() - event_room.when_locked).total_seconds() <= settings.EVENT_ROOM_REPLY_CHOICE_EXPIRY_SECONDS)
                        print(event_room.locked_for_user is not None and event_room.locked_for_user.id == self.request.user.id)
                        print(event_room.is_replying)

                    raise HandleError.new_error(
                        ValueError,
                        user_message="You cannot start replying to this event."
                    )

                #can reply, proceed

                #unlock any other event_room that were locked for reply choices
                #also save to user_event_rooms to prevent unlocked event_rooms from being queued twice
                event_rooms = EventRooms.objects.filter(
                    locked_for_user=user
                ).select_for_update(
                    of=("self",)
                ).exclude(
                    pk=event_room_id
                )

                for event_room_row in event_rooms:

                    #prevent these event_rooms from being queued again
                    prevent_event_room_from_queuing_twice_for_reply(user, event_room_row)

                    event_room_row.when_locked = None
                    event_room_row.locked_for_user = None
                    event_room_row.is_replying = None

                    event_room_row.save()

                #confirm reply, start over when_locked
                event_room.when_locked = get_datetime_now()
                event_room.is_replying = True
                event_room.save()

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
                    'message': HandleError.get_user_message(e),
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
                    event_room.generic_status.generic_status_name == 'incomplete' and\
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
                    'message': HandleError.get_user_message(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )


    #get start/cancel reply after reply choice has already been locked for the user
    def post(self, request, *args, **kwargs):

        serializer = HandleReplyingEventRoomsSerializer(data=request.data, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': 'Invalid data.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        #proceed

        if self.user_action == "start":

            return self.start_replying_to_event_room(new_data['event_room_id'])
        
        elif self.user_action == "cancel":

            return self.cancel_replying_to_event_room(new_data['event_room_id'])
        
        else:

            raise HandleError.new_error(
                AttributeError,
                dev_message="Unrecognised user_action arg from urls.py."
            )
























#to submit likes/dislikes
#is_liked=True/False, or destroy when undone
class EventLikesDislikesAPI(generics.GenericAPIView):

    serializer_class = EventLikesDislikesSerializer
    permission_classes = [IsAuthenticated]

    #no get() needed, since likes/dislikes are tied directly to events

    #create
    def post(self, request, *args, **kwargs):

        User = get_user_model()

        if self.request.user.is_authenticated is False:

            return Response(
                data={
                    'message': 'Please log in to like and dislike events.',
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = CreateEventLikesDislikesSerializer(data=request.data, many=False)

        if serializer.is_valid() is False:

            return Response(
                data={
                    'message': 'Invalid data.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = serializer.validated_data

        #get event
        try:

            event = Events.objects.get(pk=new_data['event_id'])

        except Events.DoesNotExist:

            return Response(
                data={
                    'message': 'This event does not exist.',
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:

            if new_data['is_liked'] is None:

                #remove like/dislike
                EventLikesDislikes.objects.get(
                    event=event,
                    user=User(pk=request.user.id)
                ).delete()

            else:

                #add like/dislike
                EventLikesDislikes.objects.update_or_create(
                    event=event,
                    user=User(pk=request.user.id),
                    is_liked=new_data['is_liked']
                )

        except:

            return Response(
                data={
                    'message': '',
                },
                status=status.HTTP_400_BAD_REQUEST
            )


        return Response(
            data={
                'message': 'Success!',
            },
            status=status.HTTP_200_OK
        )




#=====END OF REST APIs=====


#=====WEB PAGES=====

#create main events, but actual creation is via EventsAPI
#handles originator events
class CreateEventRooms(TemplateView):

    template_name = 'voicewake/event_rooms/create_event_rooms.html'



#view specific event_room and its events
class GetEventRooms(TemplateView):

    template_name = 'voicewake/event_rooms/get_event_rooms.html'

    def get(self, request, *args, **kwargs):

        #get event_room
        try:

            event_room = EventRooms.objects.select_related('locked_for_user', 'generic_status').get(pk=kwargs['event_room_id'])

        except EventRooms.DoesNotExist:

            return JsonResponse(
                data={
                    'message':'Event room does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        #count how many events exist for frontend skeleton
        event_count = Events.objects.filter(
            event_room=event_room,
            generic_status__generic_status_name='ok'
        ).count()

        #check if this user is already supposed to reply
        is_this_user_replying = self.request.user.is_authenticated and\
            event_room.locked_for_user is not None and\
            request.user.id == event_room.locked_for_user.id and\
            event_room.is_replying is True
        
        #is event_room deleted
        is_deleted = event_room.generic_status.generic_status_name == 'deleted'

        return render(
            request,
            template_name=self.template_name,
            context={
            'event_room_reply_choice_expiry_seconds': settings.EVENT_ROOM_REPLY_CHOICE_EXPIRY_SECONDS,
            'event_room_reply_expiry_seconds': settings.EVENT_ROOM_REPLY_EXPIRY_SECONDS,
            'event_room': event_room,
            'is_deleted': is_deleted,
            'is_deleted_json': json.dumps(is_deleted),
            'event_count': json.dumps(event_count),
            'is_this_user_replying': json.dumps(is_this_user_replying),
            }
        )



#list event_rooms, for general browsing
class ListEventRooms(TemplateView):

    template_name = 'voicewake/event_rooms/list_event_rooms.html'

    def get(self, request, *args, **kwargs):

        return render(
            request,
            template_name=self.template_name,
            context={
            'event_room_reply_choice_expiry_seconds': settings.EVENT_ROOM_REPLY_CHOICE_EXPIRY_SECONDS,
            'event_room_reply_expiry_seconds': settings.EVENT_ROOM_REPLY_EXPIRY_SECONDS,
            }
        )



#=====END OF WEB PAGES=====
