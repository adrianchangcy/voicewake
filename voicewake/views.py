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



#if empty db, run this once
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
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id
            ''',
            params=(
                self.request.user.id,
                self.request.user.id,
                True
            )
        )

        return events

    #excludes event_room started by user
    def get_queryset_by_random_incomplete(self):

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
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id
            LIMIT %s
            ''',
            params=(
                self.request.user.id,
                'incomplete',
                self.request.user.id,
                self.request.user.id,
                self.request.user.id,
                INCOMPLETE_EVENT_ROOMS_PER_ROLL,
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
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id
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
            GROUP BY events.id, event_rooms.id, event_tones.id, generic_statuses.id
            ''',
            params=(
                self.request.user.id,
                self.kwargs['event_room_id']
            )
        )

        return events

    def unlock_event_rooms_from_past_reply_choices(self):

        event_rooms = EventRooms.objects.filter(
            locked_for_user=AuthUser(pk=self.request.user.id)
        )
        
        auth_user = AuthUser(pk=self.request.user.id)
        datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))

        for event_room in event_rooms:

            #prevent these event_rooms from being queued again
            prevent_event_room_from_queuing_twice_for_reply(auth_user, event_room)

            #unlock
            event_room.when_locked = None
            event_room.locked_for_user = None
            event_room.is_replying = None

            event_room.save()

    def lock_event_rooms_for_reply_choices(self, events):

        event_room_ids = []
        datetime_now = get_datetime_now()

        for event in events:

            if event.event_room.id not in event_room_ids:

                event_room_ids.append(event.event_room.id)

                #lock for reply choices
                event.event_room.when_locked = datetime_now
                event.event_room.locked_for_user = AuthUser(pk=self.request.user.id)
                event.event_room.is_replying = False
                event.event_room.save()

        return True

    def check_user_can_create_event_room(self):

        #this is for "10 max new posts every __", which in this case is every hour
        # checkpoint_datetime = datetime.now().astimezone(tz=ZoneInfo('UTC')).strftime('%Y-%m-%d %H:00:00 %z')
        # checkpoint_datetime = datetime.strptime(checkpoint_datetime, '%Y-%m-%d %H:%M:%S %z')

        return True

    def check_user_can_reply_event_room(self, event_room_id):

        event_room = EventRooms.objects.select_related('locked_for_user').get(
            pk=event_room_id
        )

        if\
            event_room.locked_for_user is not None and\
            event_room.locked_for_user.id == self.request.user.id and\
            event_room.is_replying is True\
        :

            return True
        
        return False

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

            if row.event_role.event_role_name == 'originator':

                sorted_events[event_room_id.index(row.event_room.id)]['originator'] = row

            else:

                sorted_events[event_room_id.index(row.event_room.id)]['responder'].append(row)

        return sorted_events

    def get(self, request, *args, **kwargs):

        if 'event_room_id' in kwargs:

            return Response(
                GetEventRoomsSerializer(
                    self.sort_events(self.get_queryset_by_event_room()),
                    many=True
                ).data
            )
        
        elif 'generic_status_name' in kwargs and kwargs['generic_status_name'] == 'incomplete':

            if is_user_logged_in(request) is False:

                return Response(status=status.HTTP_401_UNAUTHORIZED)

            #check if user is replying to anything
            #we want event_room.id if there is any
            if check_user_is_replying(request) is True:

                return Response(
                    GetEventRoomsSerializer(
                        self.sort_events(self.get_queryset_by_is_replying()),
                        many=True
                    ).data,
                )

            #not replying, can unlock previous choices if any
            self.unlock_event_rooms_from_past_reply_choices()

            #get events
            events = self.get_queryset_by_random_incomplete()

            if len(events) == 0:

                return Response(
                    GetEventRoomsSerializer(
                        [],
                        many=True
                    ).data
                )
            
            #lock events
            self.lock_event_rooms_for_reply_choices(events)

            #return events sorted by event_rooms
            return Response(
                GetEventRoomsSerializer(
                    self.sort_events(events),
                    many=True
                ).data
            )
        
        else:

            return Response(
                GetEventRoomsSerializer(
                    [],
                    many=True
                ).data,
                status=status.HTTP_400_BAD_REQUEST
            )

    def post(self, request, *args, **kwargs):

        #deserialize
        serializer = CreateEventsSerializer(data=request.data, many=False)

        #validate
        if serializer.is_valid() is False:

            return Response(data={}, status=status.HTTP_400_BAD_REQUEST)
        
        new_data = serializer.validated_data

        auth_user = AuthUser.objects.get(pk=request.user.id)

        #determine if originator/responder, then create/get event_room
        #generic_status is handled by default, so it is skipped here
        if new_data['is_originator'] is True:

            #check if event_room limit is not yet reached
            if self.check_user_can_create_event_room() is False:

                return Response(data={}, status=status.HTTP_412_PRECONDITION_FAILED)

            #proceed
            event_role = EventRoles.objects.get(event_role_name='originator')

            event_room = EventRooms.objects.create(
                event_room_name=new_data['event_room_name'],
                generic_status=GenericStatuses.objects.get(generic_status_name='incomplete'),
                created_by=auth_user
            )

        else:

            #check if this user is already attached beforehand
            if self.check_user_can_reply_event_room(new_data['event_room_id']) is False:

                return Response(data={}, status=status.HTTP_412_PRECONDITION_FAILED)

            #proceed
            event_role = EventRoles.objects.get(event_role_name='responder')

            try:

                event_room = EventRooms.objects.get(pk=new_data['event_room_id'])

                #mark as completed, remove lock
                event_room.generic_status = GenericStatuses.objects.get(generic_status_name='completed')
                event_room.when_locked = None
                event_room.locked_for_user = None
                event_room.is_replying = None

                event_room.save()

                #prevent from being queued twice
                prevent_event_room_from_queuing_twice_for_reply(auth_user, event_room)

            except EventRooms.DoesNotExist:

                return Response(data={}, status=status.HTTP_400_BAD_REQUEST)
        
        #event_tone
        try:

            event_tone = EventTones.objects.get(pk=new_data['event_tone_id'])

        except EventTones.DoesNotExist:

            return Response(data={}, status=status.HTTP_400_BAD_REQUEST)

        #create event, excluding audio_file and event_room
        #generic_status is handled by default, so it is skipped here
        new_event = Events.objects.create(
            user=auth_user,
            event_role=event_role,
            event_tone=event_tone,
            audio_volume_peaks=new_data['audio_volume_peaks'],
            audio_file_seconds=new_data['audio_file_seconds'],
            event_room=event_room
        )

        #we delay saving audio_file, as we want when_created for audio_file's path
        new_event.audio_file = new_data['audio_file']
        new_event.save()

        return Response(
            {
                'data': {
                    'event_room_id': event_room.id
                },
                'message': '',
            },
            status.HTTP_201_CREATED
        )



#to handle specific actions related to user
class UserActionsAPI(generics.GenericAPIView):

    serializer_class = UserActionsSerializer
    permission_classes = [IsAuthenticated]

    #202 success, 205 reset due to user inactivity
    def start_replying_to_event_room(self, event_room_id):

        #check if user is replying to any other event_room
        if check_user_is_replying(request=self.request, exclude_event_room_id=event_room_id) is True:

            return Response(status=status.HTTP_412_PRECONDITION_FAILED)

        #get event_room
        try:

            event_room = EventRooms.objects.select_related(
                'generic_status', 'locked_for_user'
            ).get(
                pk=event_room_id
            )

        except EventRooms.DoesNotExist:

            return Response(status=status.HTTP_404_NOT_FOUND)
        
        auth_user = AuthUser(self.request.user.id)
        
        #check if incomplete
        if event_room.generic_status.generic_status_name != 'incomplete':

            return Response(status=status.HTTP_412_PRECONDITION_FAILED)
        
        #check if locked for someone else
        if event_room.locked_for_user is not None and event_room.locked_for_user.id != self.request.user.id:

            return Response(status=status.HTTP_412_PRECONDITION_FAILED)
        
        #check if user has queued this event_room before
        user_event_room_count = UserEventRooms.objects.filter(
            user=auth_user,
            event_room__id=event_room_id,
            is_excluded_for_reply=True
        ).count()
        
        if user_event_room_count > 0:

            return Response(status=status.HTTP_412_PRECONDITION_FAILED)
        
        #unlock any other event_room that were locked for reply choices
        #also save to user_event_rooms to prevent unlocked event_rooms from being queued twice
        event_rooms = EventRooms.objects.filter(
            locked_for_user=auth_user
        ).exclude(
            pk=event_room_id
        )

        for event_room_row in event_rooms:

            #prevent these event_rooms from being queued again
            prevent_event_room_from_queuing_twice_for_reply(auth_user, event_room_row)

            #unlock
            event_room_row.when_locked = None
            event_room_row.locked_for_user = None
            event_room_row.is_replying = None

            event_room_row.save()

        #we get time difference to determine user being inactive for too long
        #when_locked is used for still-active pinging
        if event_room.when_locked is not None:

            minutes_passed = (get_datetime_now() - event_room.when_locked).total_seconds() / 60

            if minutes_passed >= REPLY_INACTIVE_MAX_MINUTES:

                event_room.locked_for_user = None
                event_room.is_replying = None
                event_room.when_locked = None

                event_room.save()
                return Response(status=status.HTTP_205_RESET_CONTENT)

        #start replying or to update when_locked, same thing
        #we don't check for is_replying=False to allow for instant reply when necessary
        event_room.locked_for_user = auth_user
        event_room.is_replying = True
        event_room.when_locked = get_datetime_now()

        event_room.save()
        return Response(status=status.HTTP_202_ACCEPTED)

    #205 success
    def cancel_replying_to_event_room(self, event_room_id):

        #get event_room
        try:

            event_room = EventRooms.objects.select_related(
                'generic_status', 'locked_for_user'
            ).get(
                pk=event_room_id
            )

        except EventRooms.DoesNotExist:

            return Response(status=status.HTTP_404_NOT_FOUND)
        
        #check if incomplete
        if event_room.generic_status.generic_status_name != 'incomplete':

            return Response(status=status.HTTP_412_PRECONDITION_FAILED)
        
        #check if someone else is replying
        #also cannot cancel if event_room is not locked
        if event_room.locked_for_user is None or event_room.locked_for_user.id != self.request.user.id:

            return Response(status=status.HTTP_412_PRECONDITION_FAILED)
        
        #cancel replying
        event_room.locked_for_user = None
        event_room.is_replying = None
        event_room.when_locked = None

        event_room.save()

        #prevent repeated queue
        prevent_event_room_from_queuing_twice_for_reply(
            AuthUser(pk=self.request.user.id),
            event_room
        )

        return Response(status=status.HTTP_205_RESET_CONTENT)

    def post(self, request, *args, **kwargs):

        serializer = UserActionsSerializer(data=request.data, many=False)

        if serializer.is_valid() is False:

            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        new_data = serializer.validated_data

        if 'event_room_id' in new_data and 'to_reply' in new_data and type(new_data['to_reply']) is bool:

            if new_data['to_reply'] is True:

                return self.start_replying_to_event_room(event_room_id=new_data['event_room_id'])

            else:

                return self.cancel_replying_to_event_room(event_room_id=new_data['event_room_id'])

        else:

            return Response(status=status.HTTP_400_BAD_REQUEST)



#to submit likes/dislikes
#is_liked=True/False, or destroy when undone
class EventLikesDislikesAPI(generics.GenericAPIView):

    serializer_class = EventLikesDislikesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    #create
    def post(self, request, *args, **kwargs):

        if is_user_logged_in(request) is False:

            return Response(status=status.HTTP_401_UNAUTHORIZED)

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

        #get event_room
        try:

            event_room = EventRooms.objects.select_related('locked_for_user').get(pk=kwargs['event_room_id'])

        except EventRooms.DoesNotExist:

            return JsonResponse({'message':'Event room does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        #originator event
        #should always have only 1 per room
        try:

            originator_event = Events.objects.select_related(
                'generic_status'
            ).get(
                event_room=event_room,
                event_role__event_role_name='originator'
            )

        except Events.DoesNotExist:

            return JsonResponse({'message':'Originator event does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        
        #check if this user is already supposed to reply
        is_this_user_replying = is_user_logged_in(request) and\
            event_room.locked_for_user is not None and\
            request.user.id == event_room.locked_for_user.id

        return render(
            request,
            template_name=self.template_name,
            context={
            'event_room': event_room,
            'originator_event': originator_event,
            'is_deleted': originator_event.generic_status.generic_status_name == 'deleted',
            'is_this_user_replying': json.dumps(is_this_user_replying),
            }
        )



#list event_rooms, for general browsing
class ListEventRooms(TemplateView):

    template_name = 'voicewake/event_rooms/list_event_rooms.html'
    queryset = None



#=====END OF WEB PAGES=====
