#here, we define helpers

#Django libraries
from django.db.models import Q, Case, When, Value, F
from django.db import connection
from django.core.files import File
from rest_framework.response import Response
from rest_framework import status
from django_otp.oath import TOTP
from django.contrib.auth import get_user_model
from django.db import transaction
from django.template.loader import get_template
from django.core.mail import send_mail
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from django.core.files.base import ContentFile

#Python libraries
from datetime import datetime, timezone, timedelta, tzinfo
from genericpath import isfile
from zoneinfo import ZoneInfo
from pydub import AudioSegment
import secrets
import time
import re
import math
import subprocess
import json
from typing import Union
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper

#app files
from .models import *



#also deletes uer_x folder if empty after deletion
#meant to serve as 'always replace' logic on "record again" action
def delete_audio_file(absolute_path):

    if os.path.exists(absolute_path) and os.path.isfile(absolute_path):

        #delete precisely the file in source path
        os.remove(absolute_path)

        #delete uer_x folder if it now has 0 files
        for root, dirs, files in os.walk(os.path.dirname(absolute_path), topdown=True):

            if len(dirs) == 0 and len(files) == 0:

                shutil.rmtree(root)

        return True

    return False


def get_datetime_now(to_string:bool=False):

    datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))

    if to_string is True:

        return datetime_now.strftime('%Y-%m-%d %H:%M:%S %z')
    
    return datetime_now

    #to get difference
    #minutes_passed = (get_datetime_now() - event_room.when_locked).total_seconds() / 60
    #hours_passed = (get_datetime_now() - event_room.when_locked).total_seconds() / 60 / 60

    #to format into queryset and/or sql-friendly format:
    #get_datetime_now().strftime('%Y-%m-%d %H:%M:%S %z')


def remove_all_whitespace(string_value):

    return re.sub(r'\s+', '', string_value)


def has_numbers_only(string_value):

    return re.match(r'^[0-9]+$', string_value) is not None


def construct_timed_out_message(seconds:float, text_before_timeout='', text_after_timeout=''):

        timeout_pretty_minutes = seconds / 60
        timeout_pretty_seconds = seconds % 60

        if timeout_pretty_minutes > 0 and timeout_pretty_seconds > 0:

            return '''
                %s%s minutes and %s seconds%s
                ''' % (
                    text_before_timeout,
                    str(timeout_pretty_minutes),
                    str(timeout_pretty_seconds),
                    text_after_timeout
                )

        elif timeout_pretty_minutes > 0:

            return '''
                %s%s minutes%s
                ''' % (
                    text_before_timeout,
                    str(timeout_pretty_minutes),
                    text_after_timeout
                )

        elif timeout_pretty_seconds > 0:

            return '''
                %s%s seconds%s
                ''' % (
                    text_before_timeout,
                    str(timeout_pretty_seconds),
                    text_after_timeout
                )
        
        return ''


def is_user_banned(request):

    #??
    return False


def check_user_is_replying(request, excluded_event_room_id=None):

    User = get_user_model()

    #check if user is replying to anything
    if excluded_event_room_id is None:

        the_count = EventRooms.objects.filter(
            locked_for_user=User(pk=request.user.id),
            is_replying=True
        ).count()

    else:

        the_count = EventRooms.objects.filter(
            locked_for_user=User(pk=request.user.id),
            is_replying=True
        ).exclude(
            pk=excluded_event_room_id
        ).count()

    return the_count > 0


def group_events_into_event_rooms(events:Events)->list:

    if len(events) == 0 or events is None:

        return []

    sorted_events = []
    event_room_id = []  #simpler way to check and get element position in sorted_events

    for row in events:

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


def prevent_event_room_from_queuing_twice_for_reply(user, event_rooms:list):

    datetime_now = get_datetime_now()
    user_event_rooms = []
    event_room_ids = []

    for event_room in event_rooms:

        event_room_ids.append(event_room.id)

        user_event_room = UserEventRooms(
            user=user,
            event_room=event_room,
            is_excluded_for_reply=True,
            when_created=datetime_now
        )

        if user_event_room not in user_event_rooms:

            user_event_rooms.append(user_event_room)

    #create rows if they don't yet exist
    UserEventRooms.objects.bulk_create(
        user_event_rooms,
        ignore_conflicts=True
    )

    #do extra update just in case row already existed during bulk_create
    UserEventRooms.objects.filter(
        user=user,
        event_room_id__in=event_room_ids
    ).update(
        is_excluded_for_reply=True
    )


def get_default_verify_otp_response():

    #always return this Response when error to give 0 clues on whether user exists or not
    return Response(
        data={
            'message': "Your entered OTP is either incorrect, or you've reached the maximum attempts and should try again later.",
            'verify_otp_success': False
        },
        status=status.HTTP_400_BAD_REQUEST
    )


def get_default_create_otp_response(email):

    #always return this Response when error to give 0 clues on whether user exists or not
    return Response(
        data={
            'message': 'Verification code has been sent to %s.' % (email),
        },
        status=status.HTTP_200_OK
    )



#not advisable to group functions via class,
#it's better to create modules (files) to group functions together
def custom_error(error_class:Exception, dev_message="", user_message="")->Exception:

    #demo
    # try:
    #     raise custom_error(ValueError, "yo fix this", "hehe oops")
    # except ValueError as e:
    #     print(e.args[0]['dev_message'])

    return error_class({
        "dev_message": dev_message,
        "user_message": user_message
    })

def get_user_message_from_custom_error(new_error:Exception)->str:

    try:
        return new_error.args[0]['user_message']
    except:
        return ""

def get_dev_message_from_custom_error(new_error:Exception)->str:

    try:
        return new_error.args[0]['dev_message']
    except:
        return ""



class PrepareTestData:

    #we don't use hours_ago parameter
    #because our models use auto_now_add, which cannot be overriden
    #too lazy to replace auto_now_add=True with default=get_datetime_now(), since only tests would currently justify this
    def __init__(self, for_test:bool=True):

        #FYI, when running tests, settings.DEBUG is False
        if settings.DEBUG is True or for_test is True:
            
            pass

        else:

            raise RuntimeError('You cannot use PrepareTestData when settings.DEBUG is not True.')


    def prepare_users(self, user_quantity:int, offset:int=0):

        #offset is for when you add more users on top of existing users made with this same function

        for x in range(offset, offset + user_quantity):

            get_user_model().objects.create_user(email="user"+str(x)+"@gmail.com", username="user"+str(x))


    def prepare_test_data_event_rooms(
        self,
        originator_username, responder_username='',
        incomplete_count=0, completed_count=0,
    ):
        
        if completed_count > 0 and len(responder_username) == 0:

            raise ValueError('Requested completed event_rooms but missing responder_username.')

        #prepare fake audio column values
        audio_file = "/audio_test.mp3"
        audio_volume_peaks = [
            0.32, 0.47, 0.76, 0.75, 0.79, 0.59, 0.78, 0.83, 0.85, 0.77,
            0.62, 0.69, 0.97, 0.96, 0.97, 0.96, 0.96, 0.63, 0.47, 0.0
        ]
        audio_duration_s = 26

        #prepare relevant values
        datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))
        event_role_originator = EventRoles.objects.get(event_role_name='originator')
        event_role_responder = EventRoles.objects.get(event_role_name='responder')
        originator_user = get_user_model().objects.get(username_lowercase=originator_username.lower())
        responder_user = None
        generic_status_ok = GenericStatuses.objects.get(generic_status_name='ok')
        generic_status_incomplete = GenericStatuses.objects.get(generic_status_name='incomplete')
        generic_status_completed = GenericStatuses.objects.get(generic_status_name='completed')
        event_tone = EventTones.objects.first()

        if len(responder_username) > 0:

            responder_user = get_user_model().objects.get(username_lowercase=responder_username.lower())


        #create incomplete event rooms
        bulk_event_rooms = []

        for x in range(0, incomplete_count):

            event_room_name = "incomplete #" + str(x) + " by " + originator_username

            bulk_event_rooms.append(EventRooms(
                event_room_name=event_room_name,
                created_by=originator_user,
                generic_status=generic_status_incomplete,
            ))

        bulk_event_rooms = EventRooms.objects.bulk_create(bulk_event_rooms)

        #create incomplete events
        bulk_events = []

        for x in range(0, incomplete_count):

            bulk_events.append(Events(
                user=originator_user,
                event_role=event_role_originator,
                audio_file=audio_file,
                audio_volume_peaks=audio_volume_peaks,
                audio_duration_s=audio_duration_s,
                generic_status=generic_status_ok,
                event_room=bulk_event_rooms[x],
                event_tone=event_tone
            ))

        Events.objects.bulk_create(bulk_events)

        #create completed event rooms
        bulk_event_rooms = []

        for x in range(0, completed_count):

            event_room_name = "completed #" + str(x) + " by " + originator_username

            bulk_event_rooms.append(EventRooms(
                event_room_name=event_room_name,
                created_by=originator_user,
                generic_status=generic_status_completed,
            ))

        bulk_event_rooms = EventRooms.objects.bulk_create(bulk_event_rooms)

        #create completed events
        bulk_events = []

        for x in range(0, completed_count):

            bulk_events.append(Events(
                user=originator_user,
                event_role=event_role_originator,
                audio_file=audio_file,
                audio_volume_peaks=audio_volume_peaks,
                audio_duration_s=audio_duration_s,
                generic_status=generic_status_ok,
                event_room=bulk_event_rooms[x],
                event_tone=event_tone
            ))

            bulk_events.append(Events(
                user=responder_user,
                event_role=event_role_responder,
                audio_file=audio_file,
                audio_volume_peaks=audio_volume_peaks,
                audio_duration_s=audio_duration_s,
                generic_status=generic_status_ok,
                event_room=bulk_event_rooms[x],
                event_tone=event_tone
            ))

        Events.objects.bulk_create(bulk_events)

        #create user_event_rooms to prevent responders from queuing the same originators twice
        bulk_user_event_rooms = []

        for event_room in bulk_event_rooms:

            bulk_user_event_rooms.append(
                UserEventRooms(
                    event_room=event_room,
                    user=responder_user
                )
            )

        bulk_user_event_rooms = UserEventRooms.objects.bulk_create(bulk_user_event_rooms)


    def prepare_test_data_one_user_likes_dislikes(
        self, action_username, username_of_events, like_percentage, dislike_percentage
    ):
        
        if (like_percentage + dislike_percentage) > 1:

            raise ValueError('like_percentage and dislike_percentage can only total from 0 to 1')
        
        action_user = get_user_model().objects.get(username_lowercase=action_username)
        user_of_events = get_user_model().objects.get(username_lowercase=username_of_events)
        datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))

        #get events
        events = Events.objects.filter(user=user_of_events)

        if len(events) == 0:

            raise Events.DoesNotExist

        #create likes
        bulk_likes = []
        likes_floor = math.floor(like_percentage * len(events))

        for x in range(0, likes_floor):

            bulk_likes.append(
                EventLikesDislikes(
                    event=events[x],
                    user=action_user,
                    is_liked=True,
                )
            )

            #update count
            events[x].like_count += 1

        EventLikesDislikes.objects.bulk_create(bulk_likes)

        #create dislikes
        bulk_dislikes = []

        for x in range(likes_floor, len(events)):

            bulk_dislikes.append(
                EventLikesDislikes(
                    event=events[x],
                    user=action_user,
                    is_liked=False,
                )
            )

            #update count
            events[x].dislike_count += 1

        EventLikesDislikes.objects.bulk_create(bulk_dislikes)

        #update count
        Events.objects.bulk_update(events, ["like_count", "dislike_count"])


    #your target user should not have existing events
    def prepare_test_data_for_bans(
        self, target_username:str='', backup_username:str='',
        events_to_ban_quantity:int=10, events_not_to_ban_quantity:int=6,
        reporting_user_quantity:int=1
    ):

        if (events_to_ban_quantity % 2) != 0 or (events_not_to_ban_quantity % 2) != 0:

            raise ValueError('Make sure events_to_ban_quantity and events_not_to_ban_quantity are even numbers for consistency.')

        expected_events_count = events_to_ban_quantity + events_not_to_ban_quantity

        self.prepare_test_data_event_rooms(
            originator_username=target_username,
            incomplete_count=int(expected_events_count/2),
            completed_count=0,
        )

        self.prepare_test_data_event_rooms(
            originator_username=backup_username,
            responder_username=target_username,
            incomplete_count=0,
            completed_count=int(expected_events_count/2),
        )

        #get events
        events = Events.objects.filter(user__username_lowercase=target_username.lower())

        #excluding this causes bug
        #i.e. events is treated as subquery in delete(), and for-loop executes events only after deletion
        #hence EventLikesDislikes violating unique constraint
        print(str(len(events)) + ' events ready to evaluate')

        #reset likes dislikes for these events
        EventLikesDislikes.objects.filter(event__in=events).delete()

        #prepare to achieve like dislike ratio
        bulk_event_likes_dislikes = []
        bulk_event_reports = []
        expected_like_count = math.floor((settings.BAN_EVENT_DISLIKE_COUNT / settings.BAN_EVENT_DISLIKE_RATIO) - settings.BAN_EVENT_DISLIKE_COUNT)
        expected_dislike_count = settings.BAN_EVENT_DISLIKE_COUNT

        #make sure we have sufficient users for dislike count
        user_count = get_user_model().objects.all().count()

        if user_count < (expected_like_count + expected_dislike_count + reporting_user_quantity):

            self.prepare_users(
                user_quantity=(expected_like_count + expected_dislike_count + reporting_user_quantity - user_count),
                offset=user_count
            )

        #get users
        users = get_user_model().objects.all().order_by('id')[:(expected_like_count + expected_dislike_count + reporting_user_quantity)]

        #update Events.when_created
        when_created = get_datetime_now() - timedelta(seconds=(settings.BAN_EVENT_AGE_SECONDS * 2))

        for x in range(events_to_ban_quantity):

            #create likes
            for xx in range(expected_like_count):

                bulk_event_likes_dislikes.append(
                    EventLikesDislikes(
                        user=users[xx],
                        is_liked=True,
                        event=events[x]
                    )
                )

            #create dislikes
            for xx in range(expected_like_count, (expected_like_count + expected_dislike_count)):

                bulk_event_likes_dislikes.append(
                    EventLikesDislikes(
                        user=users[xx],
                        is_liked=False,
                        event=events[x]
                    )
                )

            #update events
            events[x].when_created = when_created
            events[x].is_banned = False

            #create event_reports
            for xx in range(
                (expected_like_count + expected_dislike_count),
                (expected_like_count + expected_dislike_count + reporting_user_quantity)
            ):

                bulk_event_reports.append(EventReports(
                    reported_event=events[x],
                    user=users[xx]
                ))

        #update db
        EventLikesDislikes.objects.bulk_create(bulk_event_likes_dislikes)
        Events.objects.bulk_update(events, ('when_created', 'is_banned',))
        EventReports.objects.bulk_create(bulk_event_reports)

        #to clear these data
        '''
            UPDATE events SET event_room_id=NULL WHERE is_banned IS TRUE;
            DELETE FROM user_event_rooms WHERE event_room_id IN (SELECT event_room_id FROM events WHERE is_banned IS TRUE);
            DELETE FROM event_rooms WHERE id NOT IN (SELECT event_room_id FROM events WHERE event_room_id IS NOT NULL);
            DELETE FROM event_likes_dislikes WHERE event_id IN (SELECT id FROM events WHERE is_banned IS TRUE);
            DELETE FROM events WHERE event_room_id IS NULL;
            UPDATE voicewake_user SET banned_until=NULL WHERE username_lowercase='oompa';
        '''

        #to clear all data related to specific user in this context
        '''
            UPDATE events SET event_room_id=NULL WHERE event_room_id IN (
                SELECT event_room_id FROM events WHERE user_id = (
                    SELECT id FROM voicewake_user WHERE username_lowercase='oompa'
                )
            );
            DELETE FROM user_event_rooms WHERE event_room_id NOT IN (SELECT event_room_id FROM events WHERE event_room_id IS NOT NULL);
            DELETE FROM event_likes_dislikes WHERE event_id IN (SELECT id FROM events WHERE event_room_id IS NULL);
            DELETE FROM event_rooms WHERE id NOT IN (SELECT event_room_id FROM events WHERE event_room_id IS NOT NULL);
            DELETE FROM events WHERE event_room_id IS NULL;
        '''


    def prepare_test_data_for_blocking_users(self, username:str='', user_quantity:int=10):

        #check if we have enough users, excluding the user blocking other users
        if (get_user_model().objects.all().count() - 1) < user_quantity:

            raise ValueError('Insufficient users.')
        
        #main user
        main_user = get_user_model().objects.get(username_lowercase=username.lower())

        #get users
        users = get_user_model().objects.all().order_by('id')[:user_quantity]

        blocked_users = []

        for user in users:

            blocked_users.append(UserBlocks(
                user=main_user,
                blocked_user=user
            ))

        UserBlocks.objects.bulk_create(blocked_users)


    def prepare_test_data_for_frontend_browse(self):

        #target user
            #originator: 2 incomplete, 2 completed, 2 banned
            #responder: 2 incomplete, 2 completed, 2 banned

        #get users
        target_user = get_user_model().objects.get(username_lowercase='user0')
        backup_user = get_user_model().objects.get(username_lowercase='user1')
        backup_user_2 = get_user_model().objects.get(username_lowercase='user2')
        backup_user_3 = get_user_model().objects.get(username_lowercase='user3')

        #prepare info for events
        #prepare fake audio column values
        audio_file = "/audio_test.mp3"
        audio_volume_peaks = [
            0.32, 0.47, 0.76, 0.75, 0.79, 0.59, 0.78, 0.83, 0.85, 0.77,
            0.62, 0.69, 0.97, 0.96, 0.97, 0.96, 0.96, 0.63, 0.47, 0.0
        ]
        audio_duration_s = 26

        #prepare relevant values
        datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))
        event_role_originator = EventRoles.objects.get(event_role_name='originator')
        event_role_responder = EventRoles.objects.get(event_role_name='responder')
        generic_status_ok = GenericStatuses.objects.get(generic_status_name='ok')
        generic_status_incomplete = GenericStatuses.objects.get(generic_status_name='incomplete')
        generic_status_completed = GenericStatuses.objects.get(generic_status_name='completed')
        generic_status_deleted = GenericStatuses.objects.get(generic_status_name='deleted')
        event_tone = EventTones.objects.first()

        def bulk_create_events(event_details):

            bulk_events = []

            for row in event_details:

                bulk_events.append(Events(
                    user=row['user'],
                    event_role=row['event_role'],
                    audio_file=audio_file,
                    audio_volume_peaks=audio_volume_peaks,
                    audio_duration_s=audio_duration_s,
                    event_room=row['event_room'],
                    generic_status=row['generic_status'],
                    is_banned=row['is_banned'],
                    event_tone=event_tone
                ))

            list(Events.objects.bulk_create(bulk_events))

        event_details = []

        #create 2 incomplete originator for target user

        event_room_1 = EventRooms.objects.create(
            event_room_name='target_user incomplete #1',
            created_by=target_user,
            generic_status=generic_status_incomplete,
        )
        event_room_2 = EventRooms.objects.create(
            event_room_name='target_user incomplete #2',
            created_by=target_user,
            generic_status=generic_status_incomplete,
        )

        event_details = [
            {'event_room': event_room_1, 'user': target_user, 'event_role': event_role_originator, 'generic_status': generic_status_ok, 'is_banned': False},
            {'event_room': event_room_2, 'user': target_user, 'event_role': event_role_originator, 'generic_status': generic_status_ok, 'is_banned': False},
        ]

        bulk_create_events(event_details)

        #create 2 originator completed for target user

        event_room_1 = EventRooms.objects.create(
            event_room_name='target_user completed #1',
            created_by=target_user,
            generic_status=generic_status_completed,
        )
        event_room_2 = EventRooms.objects.create(
            event_room_name='target_user completed #2',
            created_by=target_user,
            generic_status=generic_status_completed,
        )

        event_details = [
            {'event_room': event_room_1, 'user': target_user, 'event_role': event_role_originator, 'generic_status': generic_status_ok, 'is_banned': False},
            {'event_room': event_room_1, 'user': backup_user, 'event_role': event_role_responder, 'generic_status': generic_status_ok, 'is_banned': False},
            {'event_room': event_room_2, 'user': target_user, 'event_role': event_role_originator, 'generic_status': generic_status_ok, 'is_banned': False},
            {'event_room': event_room_2, 'user': backup_user, 'event_role': event_role_responder, 'generic_status': generic_status_ok, 'is_banned': False},
        ]

        bulk_create_events(event_details)

        #create 2 completed, but originator is banned

        event_room_1 = EventRooms.objects.create(
            event_room_name='target_user completed, target_user banned #1',
            created_by=target_user,
            generic_status=generic_status_deleted,
        )
        event_room_2 = EventRooms.objects.create(
            event_room_name='target_user completed, target_user banned #2',
            created_by=target_user,
            generic_status=generic_status_deleted,
        )

        event_details = [
            {'event_room': event_room_1, 'user': target_user, 'event_role': event_role_originator, 'generic_status': generic_status_deleted, 'is_banned': True},
            {'event_room': event_room_1, 'user': backup_user, 'event_role': event_role_responder, 'generic_status': generic_status_ok, 'is_banned': False},
            {'event_room': event_room_2, 'user': target_user, 'event_role': event_role_originator, 'generic_status': generic_status_deleted, 'is_banned': True},
            {'event_room': event_room_2, 'user': backup_user, 'event_role': event_role_responder, 'generic_status': generic_status_ok, 'is_banned': False},
        ]

        bulk_create_events(event_details)

        #create 2 completed, but responder is banned

        event_room_1 = EventRooms.objects.create(
            event_room_name='target_user completed, backup_user banned #1',
            created_by=target_user,
            generic_status=generic_status_incomplete,
        )
        event_room_2 = EventRooms.objects.create(
            event_room_name='target_user completed, backup_user banned #2',
            created_by=target_user,
            generic_status=generic_status_incomplete,
        )

        event_details = [
            {'event_room': event_room_1, 'user': target_user, 'event_role': event_role_originator, 'generic_status': generic_status_ok, 'is_banned': False},
            {'event_room': event_room_1, 'user': backup_user, 'event_role': event_role_responder, 'generic_status': generic_status_deleted, 'is_banned': True},
            {'event_room': event_room_2, 'user': target_user, 'event_role': event_role_originator, 'generic_status': generic_status_ok, 'is_banned': False},
            {'event_room': event_room_2, 'user': backup_user, 'event_role': event_role_responder, 'generic_status': generic_status_deleted, 'is_banned': True},
        ]

        bulk_create_events(event_details)

        #create 2 completed, each has 2 banned responders previously, then 1 responder

        event_room_1 = EventRooms.objects.create(
            event_room_name='target_user completed, 2 banned responses, backup_user responded #1',
            created_by=target_user,
            generic_status=generic_status_completed,
        )
        event_room_2 = EventRooms.objects.create(
            event_room_name='target_user completed, 2 banned responses, backup_user responded #2',
            created_by=target_user,
            generic_status=generic_status_completed,
        )

        event_details = [
            {'event_room': event_room_1, 'user': target_user, 'event_role': event_role_originator, 'generic_status': generic_status_ok, 'is_banned': False},
            {'event_room': event_room_1, 'user': backup_user_2, 'event_role': event_role_responder, 'generic_status': generic_status_deleted, 'is_banned': True},
            {'event_room': event_room_1, 'user': backup_user_3, 'event_role': event_role_responder, 'generic_status': generic_status_deleted, 'is_banned': True},
            {'event_room': event_room_1, 'user': backup_user, 'event_role': event_role_responder, 'generic_status': generic_status_ok, 'is_banned': False},
            {'event_room': event_room_2, 'user': target_user, 'event_role': event_role_originator, 'generic_status': generic_status_ok, 'is_banned': False},
            {'event_room': event_room_2, 'user': backup_user_2, 'event_role': event_role_responder, 'generic_status': generic_status_deleted, 'is_banned': True},
            {'event_room': event_room_2, 'user': backup_user_3, 'event_role': event_role_responder, 'generic_status': generic_status_deleted, 'is_banned': True},
            {'event_room': event_room_2, 'user': backup_user, 'event_role': event_role_responder, 'generic_status': generic_status_ok, 'is_banned': False},
        ]

        bulk_create_events(event_details)

        #create 2 incomplete, each has 2 banned responders previously

        event_room_1 = EventRooms.objects.create(
            event_room_name='target_user incomplete, 2 responses banned #1',
            created_by=target_user,
            generic_status=generic_status_incomplete,
        )
        event_room_2 = EventRooms.objects.create(
            event_room_name='target_user incomplete, 2 responses banned #2',
            created_by=target_user,
            generic_status=generic_status_incomplete,
        )

        event_details = [
            {'event_room': event_room_1, 'user': target_user, 'event_role': event_role_originator, 'generic_status': generic_status_ok, 'is_banned': False},
            {'event_room': event_room_1, 'user': backup_user_2, 'event_role': event_role_responder, 'generic_status': generic_status_deleted, 'is_banned': True},
            {'event_room': event_room_1, 'user': backup_user_3, 'event_role': event_role_responder, 'generic_status': generic_status_deleted, 'is_banned': True},
            {'event_room': event_room_2, 'user': target_user, 'event_role': event_role_originator, 'generic_status': generic_status_ok, 'is_banned': False},
            {'event_room': event_room_2, 'user': backup_user_2, 'event_role': event_role_responder, 'generic_status': generic_status_deleted, 'is_banned': True},
            {'event_room': event_room_2, 'user': backup_user_3, 'event_role': event_role_responder, 'generic_status': generic_status_deleted, 'is_banned': True},
        ]

        bulk_create_events(event_details)


    def do_quick_start(self, quantity_scale:int=1):

        if type(quantity_scale) != int:

            raise ValueError('quantity_scale must be int.')

        #quantity_scale=1 is smallest
        #100 can cause unresponsiveness

        #create users
        self.prepare_users(20*quantity_scale)

        #create incomplete/completed event_rooms
        self.prepare_test_data_event_rooms(
            originator_username="user0",
            responder_username="user1",
            incomplete_count=100*quantity_scale,
            completed_count=50*quantity_scale,
        )
        self.prepare_test_data_event_rooms(
            originator_username="user2",
            responder_username="user3",
            incomplete_count=20*quantity_scale,
            completed_count=10*quantity_scale,
        )
        self.prepare_test_data_event_rooms(
            originator_username="user4",
            responder_username="user5",
            incomplete_count=20*quantity_scale,
            completed_count=10*quantity_scale,
        )

        #get users for bulk_create
        bulk_users = get_user_model().objects.all()

        #apply likes/dislikes to events by only user0 and user1
        bulk_event_like_dislikes = []
        bulk_user_event_rooms = []

        for user in bulk_users:

            #create likes/dislikes
            self.prepare_test_data_one_user_likes_dislikes(
                action_username=user.username,
                username_of_events="user0",
                like_percentage=0.6,
                dislike_percentage=0.4,
            )
            self.prepare_test_data_one_user_likes_dislikes(
                action_username=user.username,
                username_of_events="user1",
                like_percentage=0.7,
                dislike_percentage=0.3,
            )
            self.prepare_test_data_one_user_likes_dislikes(
                action_username=user.username,
                username_of_events="user2",
                like_percentage=0.8,
                dislike_percentage=0.2,
            )
            self.prepare_test_data_one_user_likes_dislikes(
                action_username=user.username,
                username_of_events="user3",
                like_percentage=0.9,
                dislike_percentage=0.1,
            )



#for OTP
class TOTPVerification:

    #thanks to link below
    #https://medium.com/viithiisys/creating-and-verifying-one-time-passwords-with-django-otp-861f472f602f

    def __init__(self, totp_number_of_digits, totp_validity_seconds, totp_tolerance_seconds):

        #1 byte is 8 bits, so therefore minimum 15 bytes, recommended 20 bytes
        #it seems that key must always be a new random one on every new token
        #else you will forever get the same token, all things being equal
        self.key = None

        # counter with which last token was verified.
        # Next token must be generated at a higher counter value.
        self.last_verified_counter = -1

        # this value will return True, if a token has been successfully
        # verified.
        self.verified = False

        # number of digits in a token. Default is 6.
        self.totp_number_of_digits = totp_number_of_digits

        # validity period of a token. Default is 30 seconds.
        self.token_validity_period = totp_validity_seconds

        self.token_validity_tolerance = totp_tolerance_seconds


    def totp_obj(self):

        # create a TOTP object
        totp = TOTP(
            key=self.key,
            step=self.token_validity_period,
            digits=self.totp_number_of_digits
        )

        # the current time will be used to generate a counter
        totp.time = time.time()

        return totp


    def set_key(self, key):

        self.key = key


    def create_key(self, totp_key_byte_size):

        self.key = secrets.token_bytes(totp_key_byte_size)


    def get_key(self):

        return self.key


    def generate_token(self):

        # get the TOTP object and use that to create token
        totp = self.totp_obj()

        # token can be obtained with `totp.token()`
        token = str(totp.token())
        token = token.zfill(self.totp_number_of_digits)
        return token


    def verify_token(self, token):

        try:

            # convert the input token to integer
            token = int(token)

        except ValueError:

            # return False, if token could not be converted to an integer
            self.verified = False
            print('Could not convert token to int.')

        else:

            totp = self.totp_obj()

            # check if the current counter value is higher than the value of
            # last verified counter and check if entered token is correct by
            # calling totp.verify_token()
            if ((totp.t() > self.last_verified_counter) and (totp.verify(token, tolerance=self.token_validity_tolerance))):

                # if the condition is true, set the last verified counter value
                # to current counter value, and return True
                self.last_verified_counter = totp.t()
                self.verified = True

            else:

                # if the token entered was invalid or if the counter value
                # was less than last verified counter, then return False
                self.verified = False

        return self.verified



#inherits TOTPVerification class
#always use this class in transaction.atomic()
class HandleUserOTP(TOTPVerification):

    def __init__(
        self, user_instance,
        totp_number_of_digits, totp_validity_seconds, totp_tolerance_seconds,
        otp_create_timeout_seconds, otp_max_attempts, otp_max_attempt_timeout_seconds
    ):

        self.user_instance = user_instance
        self.user_otp_instance = None
        self.otp = ''

        self.otp_create_timeout_seconds = otp_create_timeout_seconds
        self.otp_max_attempts = otp_max_attempts
        self.otp_max_attempt_timeout_seconds = otp_max_attempt_timeout_seconds

        TOTPVerification.__init__(self, totp_number_of_digits, totp_validity_seconds, totp_tolerance_seconds)


    def _set_key_if_none(self):

        if self.key is None:

            self.key = bytes(self.user_instance.totp_key)


    def get_or_create_user_otp_instance(self):

        if self.user_otp_instance is None:

            self.user_otp_instance, created = UserOTP.objects.select_for_update().get_or_create(user=self.user_instance)


    def get_user_instance(self):

        return self.user_instance


    def get_user_otp_instance(self):

        return self.user_otp_instance
    

    def reset_user_otp_instance(self):

        if self.user_otp_instance is not None:

            self.user_otp_instance.otp_last_created = None
            self.user_otp_instance.otp_attempts = 0
            self.user_otp_instance.otp_last_attempted = None
            self.user_otp_instance.save()


    def is_max_attempts_timed_out(self):

        #max attempts reached
        if self.user_otp_instance.otp_attempts >= self.otp_max_attempts and self.user_otp_instance.otp_last_attempted is not None:

            #check for timeout
            timeout_end = self.user_otp_instance.otp_last_attempted + timedelta(seconds=self.otp_max_attempt_timeout_seconds)

            if get_datetime_now() < timeout_end:

                #still under timeout
                print('Is timed out from max attempts.')
                return True

            #reset after timeout
            self.reset_user_otp_instance()
            return False
        
        return False


    def get_max_attempts_timed_out_seconds_left(self):

        if self.is_max_attempts_timed_out() is False:

            return 0
        
        timeout_end = self.user_otp_instance.otp_last_attempted + timedelta(seconds=self.otp_max_attempt_timeout_seconds)
        time_remaining = (timeout_end - get_datetime_now()).total_seconds()
        time_remaining = math.ceil(time_remaining)

        return time_remaining


    def is_creating_otp_timed_out(self):

        if self.user_otp_instance.otp_last_created is None:

            return False

        #check for timeout
        timeout_end = self.user_otp_instance.otp_last_created + timedelta(seconds=self.otp_create_timeout_seconds)

        #UserOTP will first be created with otp == ''
        if get_datetime_now() < timeout_end:

            print('Is timed out from creating OTP.')
            return True
        
        return False


    def get_creating_otp_timed_out_seconds_left(self):

        if self.is_creating_otp_timed_out() is False:

            return 0
        
        timeout_end = self.user_otp_instance.otp_last_created + timedelta(seconds=self.otp_create_timeout_seconds)
        time_remaining = (timeout_end - get_datetime_now()).total_seconds()
        time_remaining = math.ceil(time_remaining)

        return time_remaining


    def generate_and_save_otp(self):

        self._set_key_if_none()

        if self.is_creating_otp_timed_out() is True:

            return ''

        self.user_otp_instance.otp_last_created = get_datetime_now()
        self.user_otp_instance.save()

        self.otp = self.generate_token()

        return self.otp


    def verify_otp(self, otp:str):

        self._set_key_if_none()

        #reminder that is_max_attempts_timed_out() calls reset_user_otp_instance() appropriately for us
        #due to the reset, there is no point in +1 attempt, as there is not supposed to be a valid OTP anymore
        if(
            self.user_otp_instance is None or
            self.is_max_attempts_timed_out() is True or
            self.user_otp_instance.otp_last_created is None
        ):

            return False

        #check token validity
        if self.verify_token(otp) is False:

            self.user_otp_instance.otp_attempts += 1
            self.user_otp_instance.otp_last_attempted = get_datetime_now()
            self.user_otp_instance.save()
            return False
        
        #ok
        self.user_otp_instance.delete()
        self.user_otp_instance = None
        return True


    def send_otp_email(self, recipient_email, subject, direction, otp):

        #we can freely use math.ceil() as long as TOTP_TOLERANCE_SECONDS is sufficient
        otp_expiry = settings.TOTP_VALIDITY_SECONDS / 60
        otp_expiry = str(math.ceil(otp_expiry))

        email_message = get_template('email/otp.html').render(context={
            'otp_direction': direction,
            'otp': otp,
            'otp_expiry': '%s minutes' % (otp_expiry)
        })

        send_mail(
            subject=subject,
            message='',
            html_message=email_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=True
        )

        return True



class HandleAudioFile:

    def __init__(self, audio_file:Union[InMemoryUploadedFile, TemporaryUploadedFile], overwrite_source:bool):

        #we do not accept abs path, because our code overrides the passed file to save memory
        #i.e. InMemoryUploadedFile/TemporaryUploadedFile makes .save() go smoothly
        #preventing override would mean duplicating memory/disk space, and ensuring disk copy is deleted
        if overwrite_source is False:

            raise custom_error(
                ValueError,
                dev_message="Current code will always overwrite original source's bytes to save memory."
            )

        #precaution:
            #size is checked via .size at serializer/form, not here
            #if you pass absolute path, remember to call .close_audio_file()

        #in the case of mp3, both codec and format/container are the same
        #mp3 can only choose 32000/44100/48000 sample rate
        #mp3 sample rate of 44100 and 48000 has big difference in quality with minimal size difference, as long as small
        self.desired_codec = "mp3"
        self.desired_format = "mp3"
        self.desired_sample_rate = "48k"

        #max timeout seconds for subprocess
        self.subprocess_timeout_s = 10

        #dBFS has max 0dB (loudest), min of approx. 6dB per bit, e.g. 16-bit will have 96dB floor
        # >0 will cause clipping
        #since we need 0 to 1 to draw peaks at frontend, but we don't know our floor (lack of bit depth info),
        #we assume via ffmpeg's silencedetect of default -60dB
        #update 2023-08-22: -60 is too high, with peaks near 1, so trying -99
        self.dbfs_floor = -99

        self.bucket_quantity = 20

        #check type
        if type(audio_file) not in [InMemoryUploadedFile, TemporaryUploadedFile]:

            raise custom_error(
                ValueError,
                dev_message="audio_file must be of type [InMemoryUploadedFile, TemporaryUploadedFile]."
            )
        
        # if type(audio_file) == str:
            # self.audio_file = open(audio_file, "rb+")

        self.audio_file = audio_file

        #other data
        self.audio_file_duration_s = None
        self.peak_buckets = None


    def prepare_audio_file_info(self)->bool:

        self.audio_file.seek(0)

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
            input=self.audio_file.read(),
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file.seek(0)

        self.audio_file_info = json.loads(result.stdout)

        if 'duration' in self.audio_file_info['format']:

            #has duration metadata
            #round off duration to int, floor is preferred in terms of presentation
            self.audio_file_duration_s = math.floor(
                float(self.audio_file_info['format']['duration'])
            )

        else:

            #no duration metadata, get it from packets instead
            self._get_duration_from_last_packet()

        #validate everything
        self._validate_audio_file_info()

        return True


    def _get_duration_from_last_packet(self):

        #dts_time: DTS time, decides when a frame has to be decoded
        #pts_time: PTS time, describes when a frame has to be presented
        #difference only becomes important in video B-frames, i.e. frames containing references past + future frames

        self.audio_file.seek(0)

        #expect packets to have dts_time/pts_time
        #we get last packet and use pts_time as seemingly accurate total duration in seconds
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-show_packets',
                '-of', 'json',
                '-read_intervals', '999999',    #seconds, make sure is longer than file duration, 999999 is safe
                '-i', 'pipe:0',
            ],
            input=self.audio_file.read(),
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file.seek(0)

        result = json.loads(result.stdout)

        #round off duration to int, floor is preferred in terms of presentation
        self.audio_file_duration_s = math.floor(
            float(result['packets'][0]['pts_time'])
        )


    def _validate_audio_file_info(self)->bool:

        if self.audio_file_info is None:

            raise custom_error(
                ValueError,
                dev_message="Cannot validate audio_file_info when it is None."
            )
        
        #audio_file_info['streams'] can have multiple dicts if there's not only audio in it
        #e.g. a flac file from an album for test has a jpeg in it with ['index'] == 1
        #don't know whether the index order is always fixed, hence the loop

        #we don't care about codec
        #we have "-select_streams a" to tell us that no audio stream exists
        if len(self.audio_file_info['streams']) == 0:

            raise custom_error(
                ValueError,
                dev_message="File does not contain audio.",
                user_message="File does not contain audio."
            )

        if self.audio_file_duration_s < 1:

            raise custom_error(
                ValueError,
                dev_message="Duration must be more than 1s.",
                user_message="Duration must be more than 1s."
            )

        return True


    def _replace_original_audio_file_bytes_with_normalised_version(self, normalised_bytes:bytes):

        #in views.py, InMemoryUploadedFile and TemporaryUploadedFile can be written into
        #if you have issues with writing, e.g. during tests, check your mode arg in io.BytesIO(path, mode="rb+")

        #delete existing bytes
        self.audio_file.truncate(0)

        self.audio_file.seek(0)

        #write in
        #good practice to use chunks(), even when unnecessary for memory, as per docs
        for chunk in ContentFile(normalised_bytes).chunks():

            self.audio_file.write(chunk)

        self.audio_file.seek(0)


    def get_peaks_by_buckets(self) -> list[float]:

        #get duration
        #get sample rate
        #asetnsamples = (duration / x buckets) * sample rate
        #expect x + 1 buckets output, so compare second last and last bucket and select the one with higher peak

        #to get highest peak per x, add "asetnsamples=x" after amovie, i.e. chunk size, e.g. "amovie=...,asetnsamples=x,..."
        #e.g. if file is 48000Hz frequency, i.e. 48000 samples/sec, asetnsamples=48000 gives you 1 sec/bucket

        #get necessary info
        sample_rate = int(self.audio_file_info['streams'][0]['sample_rate'])

        #calculate appropriate sample rate to get bucket_quantity + 1
        #math.floor() is important to guarantee we always get surplus buckets, i.e. just compare last buckets
        #compared to math.ceil(), which may give us less buckets than we need, i.e. must maybe create last fake bucket
        asetnsamples = math.floor(self.audio_file_duration_s / self.bucket_quantity * sample_rate)
        
        #must escape ":"
        ffprobe_i = 'amovie=pipe\\\\:0,asetnsamples=%s,astats=metadata=1:reset=1' % (str(asetnsamples))

        self.audio_file.seek(0)

        #get peaks
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'error',
                '-f', 'lavfi',
                '-i', ffprobe_i,
                '-show_entries', 'frame_tags=lavfi.astats.Overall.Peak_level',
                '-of', 'json'
            ],
            input=self.audio_file.read(),
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file.seek(0)

        result = json.loads(result.stdout)

        #extract peaks
        peak_buckets = []

        for count in range(self.bucket_quantity):

            #we fill the bucket to full first, then use last stored bucket to evaluate extra buckets
            peak_to_store = 0

            #value is in dBFS, max 0, min is approx. 6dB per bit depth
            #so bigger negative value means more quiet
            peak_to_store = float(result['frames'][count]['tags']['lavfi.astats.Overall.Peak_level'])

            #prevent exceeding floor
            if peak_to_store < self.dbfs_floor:

                peak_to_store = self.dbfs_floor

            #should never have > 0dB (will produce audio clipping), mainly because we'll normalise to prevent it
            if peak_to_store > 0:
                
                raise custom_error(
                    ValueError,
                    dev_message="Peak is over 0dBFS, which will clip. Calculating peaks process has been halted.",
                    user_message="Audio normalisation had failed, as there were above 0dBFS peaks detected."
                )

            #get percentage
            # -x / -y will always be positive
            peak_to_store = peak_to_store / self.dbfs_floor

            #invert percentage
            peak_to_store = 1 - peak_to_store

            #get 0 to 1 value
            peak_to_store = peak_to_store * 1

            #truncate
            peak_to_store = float(round(peak_to_store, 2))

            #while peak_buckets is not yet full, fill until full
            if count < self.bucket_quantity:

                peak_buckets.append(peak_to_store)
                continue

            #handle extra buckets
            #store the higher peak between last stored peak and current peak
            if peak_buckets[self.bucket_quantity] < peak_to_store:

                peak_buckets[self.bucket_quantity] = peak_to_store

        self.peak_buckets = peak_buckets
        return peak_buckets


    def do_normalisation(self) -> bytes:

        #"loudnorm=I=-16:TP=-1.5:LRA=11" is from loudnorm docs on EBU R 128
        #"loudnorm=I=-23:LRA=7:TP=-2" is from ffmpeg-normalize on EU's LUFS -23 regulation
        loudnorm_args = "loudnorm=I=-23:TP=-2:LRA=7"

        #I is LUFS
        #LRA is loudness range, i.e. range between softest and loudest parts
        #TP is true peak, -2 seems common, just be sure to give enough headroom towards 0, and never over 0

        self.audio_file.seek(0)

        #first pass, get measurement
        ffmpeg_cmd = subprocess.run(
            [
                "ffmpeg",
                "-i", "pipe:0",
                "-af", loudnorm_args + ":print_format=json",
                '-f', "null", "/dev/null"
            ],
            input=self.audio_file.read(),
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file.seek(0)

        #get print string from stderr
        first_pass_data = ffmpeg_cmd.stderr.decode()

        #construct our json string
        #this will work as long as entire print string only has one {}
        first_pass_dict = re.search(r"(\{[\s\S]*\})", first_pass_data)[0]

        if first_pass_dict is None:

            raise custom_error(
                ValueError,
                dev_message="Regex could not find the data needed for first_pass_dict via regex.",
                user_message=""
            )

        #transform into proper dict
        first_pass_dict = json.loads(first_pass_dict)
        first_pass_dict = dict(first_pass_dict)

        #prepare -af values for second pass
        #can't directly .format() here, must call the variable again
        ffmpeg_cmd_af = loudnorm_args +\
            ":measured_I={0}" +\
            ":measured_LRA={1}" +\
            ":measured_TP={2}" +\
            ":measured_thresh={3}" +\
            ":offset={4}" +\
            ":linear=true:print_format=summary"
        
        ffmpeg_cmd_af = ffmpeg_cmd_af.format(
            first_pass_dict["input_i"],
            first_pass_dict["input_lra"],
            first_pass_dict["input_tp"],
            first_pass_dict["input_thresh"],
            first_pass_dict["target_offset"]
        )
        
        #do second pass, get file
        ffmpeg_cmd = subprocess.run(
            [
                "ffmpeg",
                "-i", "pipe:0",
                "-af", ffmpeg_cmd_af,
                "-ar", self.desired_sample_rate,           #sample rate; mp3 can only choose 32000/44100/48000
                # "-b:a", "124k",         #bit rate, not sure if safe/redundant/necessary
                "-c:a", self.desired_codec,          #codec; a is audio, v is video
                "-f", self.desired_format, "pipe:1"   #f is format; for disk files, can just write "my_folder/file.mp3"
            ],
            input=self.audio_file.read(),
            check=True,
            capture_output=True,
            timeout=self.subprocess_timeout_s
        )

        self.audio_file.seek(0)

        output = ffmpeg_cmd.stdout

        self._replace_original_audio_file_bytes_with_normalised_version(output)

        return output


    def close_audio_file(self):

        #must call this when you're done with .open()
        #other types will be auto-closed by Django at end of request
        self.audio_file.close()

















