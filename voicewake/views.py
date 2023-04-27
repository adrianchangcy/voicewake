from django import views
from django.http import JsonResponse, QueryDict
from django.db.models import Case, Value, When, Sum, Q, F, Count
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from django.db import connection

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.authtoken.models import Token

#class-based views
from rest_framework import viewsets, generics
    #ModelViewSet has: list, create, retrieve, update, partial_update, destroy
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from django.views.generic.list import ListView
from django.views.generic import TemplateView

#mixins
from django.contrib.auth.mixins import PermissionRequiredMixin

#Python libraries
from datetime import datetime, timezone, timedelta
import zoneinfo
import os
import json

#app files
from voicewake.forms import *
from .models import *
from .serializers import *
from .services import *

#static values for configuring throughout the app
from .static.values.values import *


#overriding ModelViewSet's check_permissions() via super() to allow permission_classes_per_method
class PermissionPolicyMixin():
    
    def check_permissions(self, request):
        try:
            # This line is heavily inspired from `APIView.dispatch`.
            # It returns the method associated with an endpoint.
            handler = getattr(self, request.method.lower())
        except AttributeError:
            handler = None

        if (
            handler
            and self.permission_classes_per_method
            and self.permission_classes_per_method.get(handler.__name__)
        ):
            self.permission_classes = self.permission_classes_per_method.get(handler.__name__)

        super().check_permissions(request)


# #TESTING AREA
# @api_view(['GET','POST'])
# # @permission_required('voicewake.can_fart', login_url='/login', raise_exception=True)
# def user_verification_options_list(request, format=None):

#     #TESTING AREA
#     #======================


#     # if request.user.is_superuser:

#     #     print('hooray')

#     # boom = UserVerificationOptions.objects.exclude(pk=1, user_verification_option_name="Instagram")

#     # if boom:

#     #     print('waddup')

#     # serializer = UserVerificationOptionsSerializer(boom, many=True)

#     # return JsonResponse(data={'user_verification_options':serializer.data}, status=status.HTTP_418_IM_A_TEAPOT)
#     # return
#     #======================

#     if request.method == 'GET':

#         user_verification_options = UserVerificationOptions.objects.all()
#         serializer = UserVerificationOptionsSerializer(user_verification_options, many=True)

#         return Response(serializer.data)

#     elif request.method == 'POST':

#         serializer = UserVerificationOptionsSerializer(data=request.data)

#         if serializer.is_valid():

#             serializer.save()
#             return JsonResponse(data={'user_verification_options':serializer.data}, status=status.HTTP_201_CREATED)

#     return JsonResponse(data={'detail':'invalid request type'}, status=status.HTTP_418_IM_A_TEAPOT)


# @api_view(['GET', 'PUT', 'DELETE'])
# def user_verification_options_details(request, id, format=None):

#     try:

#         user_verification_option = UserVerificationOptions.objects.get(pk=id)

#     except UserVerificationOptions.DoesNotExist:
        
#         return Response(status=status.HTTP_404_NOT_FOUND)

#     if request.method == 'GET':

#         serializer = UserVerificationOptionsSerializer(user_verification_option)

#         return JsonResponse({"user_verification_options":serializer.data}, safe=False)

#     elif request.method == 'PUT':

#         #request.data is just plain dict of passed data
#         #so you can manually modify it as such, e.g. request.data.update({})

#         serializer = UserVerificationOptionsSerializer(user_verification_option, data=request.data)

#         if serializer.is_valid():

#             serializer.save()
#             #you can also pass data changes into .save() in kwargs fashion:
#             # serializer.save(user_verification_option_name="clown")

#             return JsonResponse({"user_verification_option":serializer.data}, safe=False)

#     elif request.method == 'DELETE':

#         user_verification_option.delete()

#         return Response(status=status.HTTP_204_NO_CONTENT)

#     return Response(status=status.HTTP_418_IM_A_TEAPOT)


#if empty db, run this
def first_time_setup():

    from django.contrib.auth.models import Group

    if EventTones.objects.count() == 0:

        EventTones.objects.bulk_create([
            EventTones(event_tone_name='blank face', event_tone_symbol='😶'),
            EventTones(event_tone_name='plain smile', event_tone_symbol='🙂'),
            EventTones(event_tone_name='smile', event_tone_symbol='😄'),
            EventTones(event_tone_name='smiley', event_tone_symbol='😃'),
            EventTones(event_tone_name='grinning', event_tone_symbol='😀'),
            EventTones(event_tone_name='blush', event_tone_symbol='😊'),
            EventTones(event_tone_name='halo', event_tone_symbol='😇'),
            EventTones(event_tone_name='wink', event_tone_symbol='😉'),
            EventTones(event_tone_name='heart eyes', event_tone_symbol='😍'),
            EventTones(event_tone_name='kissing heart', event_tone_symbol='😘'),
            EventTones(event_tone_name='kissing flushed', event_tone_symbol='😚'),
            EventTones(event_tone_name='kissing', event_tone_symbol='😗'),
            EventTones(event_tone_name='kissing smiling eyes', event_tone_symbol='😙'),
            EventTones(event_tone_name='stuck out tongue winking eye', event_tone_symbol='😜'),
            EventTones(event_tone_name='stuck out tongue closed eyes', event_tone_symbol='😝'),
            EventTones(event_tone_name='stuck out tongue', event_tone_symbol='😛'),
            EventTones(event_tone_name='flushed', event_tone_symbol='😳'),
            EventTones(event_tone_name='grin', event_tone_symbol='😁'),
            EventTones(event_tone_name='pensive', event_tone_symbol='😔'),
            EventTones(event_tone_name='relieved', event_tone_symbol='😌'),
            EventTones(event_tone_name='unamused', event_tone_symbol='😒'),
            EventTones(event_tone_name='disappointed', event_tone_symbol='😞'),
            EventTones(event_tone_name='persevere', event_tone_symbol='😣'),
            EventTones(event_tone_name='cry', event_tone_symbol='😢'),
            EventTones(event_tone_name='joy', event_tone_symbol='😂'),
            EventTones(event_tone_name='sob', event_tone_symbol='😭'),
            EventTones(event_tone_name='sleepy', event_tone_symbol='😪'),
            EventTones(event_tone_name='disappointed relieved', event_tone_symbol='😥'),
            EventTones(event_tone_name='cold sweat', event_tone_symbol='😰'),
            EventTones(event_tone_name='sweat smile', event_tone_symbol='😅'),
            EventTones(event_tone_name='sweat', event_tone_symbol='😓'),
            EventTones(event_tone_name='weary', event_tone_symbol='😩'),
            EventTones(event_tone_name='tired face', event_tone_symbol='😫'),
            EventTones(event_tone_name='fearful', event_tone_symbol='😨'),
            EventTones(event_tone_name='scream', event_tone_symbol='😱'),
            EventTones(event_tone_name='angry', event_tone_symbol='😠'),
            EventTones(event_tone_name='rage', event_tone_symbol='😡'),
            EventTones(event_tone_name='triumph', event_tone_symbol='😤'),
            EventTones(event_tone_name='confounded', event_tone_symbol='😖'),
            EventTones(event_tone_name='laughing', event_tone_symbol='😆'),
            EventTones(event_tone_name='yum', event_tone_symbol='😋'),
            EventTones(event_tone_name='injured', event_tone_symbol='🤕'),
            EventTones(event_tone_name='mask', event_tone_symbol='😷'),
            EventTones(event_tone_name='fever', event_tone_symbol='🤒'),
            EventTones(event_tone_name='nauseating', event_tone_symbol='🤢'),
            EventTones(event_tone_name='heated', event_tone_symbol='🥵'),
            EventTones(event_tone_name='chilled', event_tone_symbol='🥶'),
            EventTones(event_tone_name='sunglasses', event_tone_symbol='😎'),
            EventTones(event_tone_name='cowboy', event_tone_symbol='🤠'),
            EventTones(event_tone_name='money face', event_tone_symbol='🤑'),
            EventTones(event_tone_name='party face', event_tone_symbol='🥳'),
            EventTones(event_tone_name='sleeping', event_tone_symbol='😴'),
            EventTones(event_tone_name='dizzy face', event_tone_symbol='😵'),
            EventTones(event_tone_name='astonished', event_tone_symbol='😲'),
            EventTones(event_tone_name='worried', event_tone_symbol='😟'),
            EventTones(event_tone_name='frowning', event_tone_symbol='😦'),
            EventTones(event_tone_name='anguished', event_tone_symbol='😧'),
            EventTones(event_tone_name='imp', event_tone_symbol='👿'),
            EventTones(event_tone_name='open mouth', event_tone_symbol='😮'),
            EventTones(event_tone_name='grimacing', event_tone_symbol='😬'),
            EventTones(event_tone_name='neutral face', event_tone_symbol='😐'),
            EventTones(event_tone_name='confused', event_tone_symbol='😕'),
            EventTones(event_tone_name='hushed', event_tone_symbol='😯'),
            EventTones(event_tone_name='smirk', event_tone_symbol='😏'),
            EventTones(event_tone_name='expressionless', event_tone_symbol='😑'),
            EventTones(event_tone_name='baby', event_tone_symbol='👶'),
            EventTones(event_tone_name='older man', event_tone_symbol='👴'),
            EventTones(event_tone_name='older woman', event_tone_symbol='👵'),
            EventTones(event_tone_name='angel', event_tone_symbol='👼'),
            EventTones(event_tone_name='princess', event_tone_symbol='👸'),
            EventTones(event_tone_name='see no evil', event_tone_symbol='🙈'),
            EventTones(event_tone_name='hear no evil', event_tone_symbol='🙉'),
            EventTones(event_tone_name='speak no evil', event_tone_symbol='🙊'),
            EventTones(event_tone_name='clown', event_tone_symbol='🤡'),
            EventTones(event_tone_name='moyai', event_tone_symbol='🗿'),
            EventTones(event_tone_name='skull', event_tone_symbol='💀'),
            EventTones(event_tone_name='alien', event_tone_symbol='👽'),
            EventTones(event_tone_name='hankey', event_tone_symbol='💩'),
            EventTones(event_tone_name='wave', event_tone_symbol='👋'),
            EventTones(event_tone_name='pray', event_tone_symbol='🙏'),
            EventTones(event_tone_name='clap', event_tone_symbol='👏'),
            EventTones(event_tone_name='muscle', event_tone_symbol='💪'),
            EventTones(event_tone_name='bow', event_tone_symbol='🙇'),
            EventTones(event_tone_name='broken heart', event_tone_symbol='💔'),
            EventTones(event_tone_name='two hearts', event_tone_symbol='💕'),
            EventTones(event_tone_name='sparkling heart', event_tone_symbol='💖'),
            EventTones(event_tone_name='revolving hearts', event_tone_symbol='💞'),
            EventTones(event_tone_name='cupid', event_tone_symbol='💘'),
            EventTones(event_tone_name='turtle', event_tone_symbol='🐢'),
            EventTones(event_tone_name='snail', event_tone_symbol='🐌'),
            EventTones(event_tone_name='octopus', event_tone_symbol='🐙'),
            EventTones(event_tone_name='four leaf clover', event_tone_symbol='🍀'),
            EventTones(event_tone_name='herb', event_tone_symbol='🌿'),
            EventTones(event_tone_name='hourglass flowing sand', event_tone_symbol='⏳'),
            EventTones(event_tone_name='hourglass', event_tone_symbol='⌛'),
            EventTones(event_tone_name='game die', event_tone_symbol='🎲'),
            EventTones(event_tone_name='checkered flag', event_tone_symbol='🏁'),
            EventTones(event_tone_name='trophy', event_tone_symbol='🏆'),
            EventTones(event_tone_name='roller coaster', event_tone_symbol='🎢'),
            EventTones(event_tone_name='rocket', event_tone_symbol='🚀'),
            EventTones(event_tone_name='keep it 100', event_tone_symbol='💯'),
        ])

    if Countries.objects.count() == 0:

        Countries.objects.create(
            country_name='United States of America',
            country_name_shortened='USA'
        )

    if Languages.objects.count() == 0:

        Languages.objects.create(
                    language_name='English',
                    language_name_shortened='ENG'
        )

    if Group.objects.count() == 0:

        Group.objects.create(
            name='regular'
        )

    if GenericStatuses.objects.count() == 0:

        GenericStatuses.objects.bulk_create([
            GenericStatuses(generic_status_name='ok'),
            GenericStatuses(generic_status_name='deleted'),
            GenericStatuses(generic_status_name='incomplete'),
            GenericStatuses(generic_status_name='completed'),
        ])

    if EventRoles.objects.count() == 0:

        EventRoles.objects.bulk_create([
            EventRoles(event_role_name='originator'),
            EventRoles(event_role_name='responder')
        ])


# @login_required(login_url='/login')
def home(request):

    return render(request, template_name='voicewake/home.html')


def sign_up(request):

    if request.method == 'POST':

        form = UserSignUpForm(request.POST)

        if form.is_valid():

            user = form.save()

            Token.objects.create(user=user)

            login(request, user)
            return redirect('/')

    else:

        #show empty form
        form = UserSignUpForm()

    return render(request, 'registration/sign_up.html', {"form":form})


#TBD
#TEST SETTING TIME ZONE
common_timezones = {
    'London': 'Europe/London',
    'Paris': 'Europe/Paris',
    'New York': 'America/New_York',
}
def set_timezone(request):

    if request.method == 'POST':
        request.session['django_timezone'] = request.POST['timezone']
        return redirect('/')
    else:
        return render(request, 'voicewake/set_timezone.html', {'timezones': common_timezones})









# class UserVerificationOptionsViewSet(PermissionRequiredMixin, viewsets.ModelViewSet):
class UserVerificationOptionsAPI(PermissionPolicyMixin, viewsets.ModelViewSet):

    # authentication_classes = [SessionAuthentication, BasicAuthentication]
    # permission_classes = [IsAuthenticated]

    #leave empty or specify ('app_name.permission_code_name1', 'app_name.permission_code_name2')
    # permission_required = ()

    permission_classes_per_method = {
        'list' : [IsAdminUser]
    }

    serializer_class = UserVerificationOptionsSerializer
    queryset = UserVerificationOptions.objects.all()


            
    #if you have a function here, you can override viewset-level configs for the function, e.g.:
    # from rest_framework.decorators import action
    # @action(detail=True, methods=['post'], permission_classes=[IsAdminOrIsSelf])



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


#we get events via event_room, as they all must belong to a room
class EventsAPI(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = GetEventsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = None

    def get_queryset_all_test(self):

        events = Events.objects.raw(
            '''
            SELECT
                events.*,
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
                    ELSE null
                    END
                ) as is_liked_by_user
            FROM events
            LEFT JOIN event_likes_dislikes ON  events.id = event_likes_dislikes.event_id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            GROUP BY events.id, event_tones.id, generic_statuses.id
            ''',
            params=(
                self.request.user.id,
            )
        )
        return events

    def get_queryset_by_random_incomplete(self):

        events = Events.objects.raw(
            '''
            SELECT
                events.*,
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
                    ELSE null
                    END
                ) as is_liked_by_user
            FROM events
            LEFT JOIN event_likes_dislikes ON  events.id = event_likes_dislikes.event_id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            WHERE events.event_room_id IN (
                SELECT event_rooms.id FROM event_rooms
                INNER JOIN generic_statuses ON event_rooms.generic_status_id = generic_statuses.id
                WHERE generic_statuses.generic_status_name=%s
                LIMIT %s
            )
            AND events.event_room_id NOT IN (
                SELECT seen_event_rooms.id FROM seen_event_rooms
                INNER JOIN event_rooms ON seen_event_rooms.event_room_id = event_rooms.id
                WHERE user_id=%s
            )
            GROUP BY events.id, event_tones.id, generic_statuses.id
            ''',
            params=(
                self.request.user.id,
                'incomplete',
                INCOMPLETE_EVENT_ROOMS_PER_ROLL,
                self.request.user.id,
            )
        )

        #lock these event_rooms
        #store these event_rooms to seen_event_rooms
        datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))
        event_rooms_for_update = []
        seen_event_rooms_for_create = []

        for event in events:

            #prepare for event_rooms lock
            event_room = EventRooms(pk=event.event_room.id)
            event_room.locked_for_user = AuthUser(pk=self.request.user.id)
            event_room.when_locked = datetime_now
            event_room.last_modified = datetime_now

            event_rooms_for_update.append(event_room)

            #prepare for seen_event_rooms create
            seen_event_room = SeenEventRooms(
                user=AuthUser(pk=self.request.user.id),
                event_room=event_room
            )

            seen_event_rooms_for_create.append(seen_event_room)

        #lock event_rooms
        EventRooms.objects.bulk_update(objs=event_rooms_for_update, fields=['locked_for_user', 'when_locked', 'last_modified'])

        #create seen_event_rooms
        SeenEventRooms.objects.bulk_create(seen_event_rooms_for_create)

        return events

    def get_queryset_by_best_completed(self):

        #this is for "10 max new posts every __", which in this case is every hour
        checkpoint_datetime = datetime.now().astimezone(tz=ZoneInfo('UTC')).strftime('%Y-%m-%d %H:00:00 %z')
        checkpoint_datetime = datetime.strptime(checkpoint_datetime, '%Y-%m-%d %H:%M:%S %z')

        events = Events.objects.raw(
            '''
            SELECT
                events.*,
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
                    ELSE null
                    END
                ) as is_liked_by_user
            FROM events
            LEFT JOIN event_likes_dislikes ON  events.id = event_likes_dislikes.event_id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            WHERE events.event_room_id IN (
                SELECT event_rooms.id FROM event_rooms
                INNER JOIN generic_statuses ON event_rooms.generic_status_id = generic_statuses.id
                WHERE generic_statuses.generic_status_name=%s
                AND event_rooms.when_created >= %s
                LIMIT %s
            )
            GROUP BY events.id, event_tones.id, generic_statuses.id
            ORDER BY like_count DESC
            ''',
            params=(
                self.request.user.id,
                'completed',
                checkpoint_datetime,
                SPECIAL_EVENT_ROOMS_QUANTITY
            )
        )

        return events
        
    def get_queryset_by_event_room(self):

        events = Events.objects.raw(
            '''
            SELECT
                events.*,
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
                    ELSE null
                    END
                ) as is_liked_by_user
            FROM events
            LEFT JOIN event_likes_dislikes ON  events.id = event_likes_dislikes.event_id
            LEFT JOIN event_tones ON events.event_tone_id = event_tones.id
            LEFT JOIN generic_statuses ON events.generic_status_id = generic_statuses.id
            WHERE events.event_room_id = %s
            GROUP BY events.id, event_tones.id, generic_statuses.id
            ''',
            params=(
                self.request.user.id,
                self.kwargs['event_room_id']
            )
        )

        return events

    def sort_events(self, queryset):

        sorted_events = []
        event_room_id = []  #simpler way to check and get element position in sorted_events

        for count, row in enumerate(queryset):

            if row.event_room.id not in event_room_id:

                sorted_events.append({
                    'event_room': row.event_room,
                    'originator': None,
                    'responder': []
                })
                event_room_id.append(row.event_room.id)

            if row.user_event_role.event_role.event_role_name == 'originator':

                sorted_events[event_room_id.index(row.event_room.id)]['originator'] = row

            else:

                sorted_events[event_room_id.index(row.event_room.id)]['responder'].append(row)

        return sorted_events

    def get(self, request, *args, **kwargs):

        if 'event_room_id' in kwargs:

            return Response(GetEventsSerializer(self.get_queryset_by_event_room(), many=True).data)
        
        elif 'generic_status_name' in kwargs and kwargs['generic_status_name'] == 'completed':

            return Response(
                GetEventRoomsSerializer(
                    self.sort_events(self.get_queryset_all_test()),
                    many=True
                ).data
            )
            # return Response(GetEventsSerializer(self.get_queryset_by_best_completed(), many=True).data)
        
        else:

            return Response(GetEventsSerializer([], many=True).data)

    def post(self, request, *args, **kwargs):
        
        #deserialize
        serializer = CreateEventsSerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(data={}, status=status.HTTP_400_BAD_REQUEST)
        
        new_data = serializer.validated_data

        #determine if originator/responder, then create/get event_room
        #generic_status is handled by default, so it is skipped here
        if new_data['is_originator'] is True:

            event_role_name = 'originator'

            event_room = EventRooms.objects.create(
                event_room_name=new_data['event_room_name'],
                generic_status=GenericStatuses.objects.get(generic_status_name='incomplete')
            )

        else:

            event_role_name = 'responder'

            try:

                event_room = EventRooms.objects.get(pk=new_data['event_room_id'])
                event_room.generic_status = GenericStatuses.objects.get(generic_status_name='completed')
                event_room.save()

            except EventRooms.DoesNotExist:

                return Response(data={}, status=status.HTTP_400_BAD_REQUEST)

        #user_event_role
        try:

            user_event_role = UserEventRoles.objects.get(
                user=AuthUser(pk = getattr(self.request.user, 'id')),
                event_role__event_role_name=event_role_name
            )

        except UserEventRoles.DoesNotExist:

            return Response(data={}, status=status.HTTP_400_BAD_REQUEST)
        
        #event_tone
        try:

            event_tone = EventTones.objects.get(pk=new_data['event_tone_id'])

        except EventTones.DoesNotExist:

            return Response(data={}, status=status.HTTP_400_BAD_REQUEST)

        #create event, excluding audio_file and event_room
        #generic_status is handled by default, so it is skipped here
        new_event = Events.objects.create(
            user_event_role=user_event_role,
            event_tone=event_tone,
            audio_volume_peaks=new_data['audio_volume_peaks'],
            event_room=event_room
        )

        #we delay saving audio_file, as we want when_created first
        new_event.audio_file = new_data['audio_file']

        new_event.save()

        #don't return super().form_valid(form), else it goes though form.save() again
        return JsonResponse(data={}, status=status.HTTP_201_CREATED)


#to submit likes/dislikes
#is_liked=True/False, or destroy when undone
class EventLikesDislikesAPI(generics.GenericAPIView):

    serializer_class = EventLikesDislikesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    #create
    def post(self, request, *args, **kwargs):

        serializer = CreateEventLikesDislikesSerializer(data=request.data, many=False)

        if serializer.is_valid() is False:

            return Response(status=status.HTTP_400_BAD_REQUEST)

        new_data = serializer.validated_data

        #get event
        try:

            event = Events.objects.get(pk=new_data['event_id'])

        except Events.DoesNotExist:

            return Response(status=status.HTTP_400_BAD_REQUEST)

        #handle is_liked
        try:

            event_like_dislike = EventLikesDislikes.objects.get(
                event=event,
                user=AuthUser(pk=request.user.id)
            )

            if new_data['is_liked'] is not None:

                event_like_dislike.is_liked = new_data['is_liked']
                event_like_dislike.save()

            else:

                event_like_dislike.delete()

        except EventLikesDislikes.DoesNotExist:

            if new_data['is_liked'] is not None:

                EventLikesDislikes.objects.create(
                    event=event,
                    user=AuthUser(pk=request.user.id),
                    is_liked=new_data['is_liked']
                )

        #even when somehow is_liked=None and row does not exist, return OK
        return Response(status=status.HTTP_200_OK)


#=====END OF REST APIs=====


#=====WEB PAGES=====

#create main events, but actual creation is via EventsAPI
#handles originator events
class CreateEventRooms(TemplateView):

    template_name = 'voicewake/event_rooms/create_event_rooms.html'
    success_url = '/'


#view specific event_room and its events
class GetEventRooms(TemplateView):

    template_name = 'voicewake/event_rooms/get_event_rooms.html'
    success_url = '/'

    def get(self, request, *args, **kwargs):

        #originator event
        #should always have only 1 per room
        try:

            originator_event = Events.objects.select_related(
                'event_room', 'generic_status', 'event_tone'
            ).get(
                event_room=EventRooms(pk=kwargs['event_room_id']),
                user_event_role__event_role__event_role_name='originator'
            )

        except Events.DoesNotExist:

            return JsonResponse({'message':'Originator event does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        
        return render(
            request,
            template_name=self.template_name,
            context={
            'originator_event': originator_event,
            'is_deleted': originator_event.generic_status.generic_status_name == 'deleted',
            }
        )


#list event_rooms, for general browsing
class ListEventRooms(ListView):

    template_name = 'voicewake/event_rooms/list_event_rooms.html'

    def get_queryset(self):

        events = [1,1]

        return events



#=====END OF WEB PAGES=====
