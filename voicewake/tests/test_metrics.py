from time import sleep
from django.test import TestCase, Client, TransactionTestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db import connection
from django.core.cache import cache

from voicewake.models import *
from voicewake.services import *
from django.db.models import Case, Value, When, Sum, Q, F, Count, BooleanField
from django.conf import settings

import math
from typing import Literal
import inspect
import time



#how to generate realistic large set of data

#create 100 users
#create incomplete/completed/deleted events
    #incomplete: user + event + audio_clip
    #completed: user*2 + event + audio_clip*2
    #deleted: user(User.is_banned=True,User.banned_until) + event + audio_clip
    #deleted: user(User.is_banned=True,User.banned_until) + user(User.is_banned=True,User.banned_until) + event + audio_clip
    #deleted: user + user(User.is_banned=True,User.banned_until) + event + audio_clip
#ensure some audio_clip_tones are not used
#apply likes and dislikes to audio clips
    #0 likes 0 dislikes
    #8 likes 0 dislikes
    #5 likes 5 dislikes
    #0 likes 8 dislikes

#test cases
    #without specifying user
        #test when rows are the newest in db
        #test when rows are the oldest in db
        #test when rows don't exist based on audio_clip
        #test when rows are in the middle in terms of when_created
        #test when rows are in the middle in terms of when_created + audio_clip_tones
    #with specific user, when user is middle in terms of when_created
        #test when rows are the newest in db
        #test when rows are the oldest in db
        #test when rows don't exist based on audio_clip
        #test when rows are in the middle in terms of when_created
        #test when rows are in the middle in terms of when_created + audio_clip_tones
    #with specific user, when user is oldest
        #test when rows are the newest in db
        #test when rows are the oldest in db
        #test when rows don't exist based on audio_clip
        #test when rows are in the middle in terms of when_created
        #test when rows are in the middle in terms of when_created + audio_clip_tones



#good balance of rows with same dates will test indexing better
#if you have too many rows to the point where it's unrealistic, space out data creation with time.sleep(1)
#if you want more realistic likes/dislikes, group audio_clips by modulus, e.g. %2 %4 %6
class RealisticBulkData():

    def __init__(
        self,
        batch_quantity=1,
        like_dislike_activitiy:Literal['low','high']='low',
    ):

        self.batch_quantity = batch_quantity
        self.bulk_create_batch_size = 200

        self.user_quantity = 10 * batch_quantity
        self.user_prefix = "testuser"
        self.user_count = 0
        self.users = []
        self.audio_file = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/audio_ok_1.mp3'
        )

        self.event_quantity = 10 * batch_quantity

        self.generic_statuses = {
            'ok': GenericStatuses.objects.get(generic_status_name='ok'),
            'incomplete': GenericStatuses.objects.get(generic_status_name='incomplete'),
            'completed': GenericStatuses.objects.get(generic_status_name='completed'),
            'deleted': GenericStatuses.objects.get(generic_status_name='deleted'),
            'processing': GenericStatuses.objects.get(generic_status_name='processing'),
        }
        self.audio_clip_roles = {
            'originator': AudioClipRoles.objects.get(audio_clip_role_name='originator'),
            'responder': AudioClipRoles.objects.get(audio_clip_role_name='responder'),
        }

        #divide audio_clip_tones into 4 quarters, choose one per quarter to exclude when creating audio_clips
        #this will allow for better index testing

        self.audio_clip_tones = AudioClipTones.objects.all()
        self.excluded_audio_clip_tones_index = []

        audio_clip_tones_per_quarter = math.floor(len(self.audio_clip_tones) / 4)

        #closest to start, but not first
        self.excluded_audio_clip_tones_index.append(1)
        #second quarter
        self.excluded_audio_clip_tones_index.append((audio_clip_tones_per_quarter*2) - 1)
        #third quarter
        self.excluded_audio_clip_tones_index.append((audio_clip_tones_per_quarter*3) - 1)
        #closest to end, but not last
        self.excluded_audio_clip_tones_index.append(len(self.audio_clip_tones) - 2)

        #we accumulate audio_clips here to later have better control on creating likes/dislikes
        self.audio_clips = []

        self.like_dislike_activity = like_dislike_activitiy
        self.like_dislike_user_group_count = 2
        self.like_count = 0
        self.dislike_count = 0
        self.like_ratio = 0


    def _check_ready(self):

        if len(self.users) == 0:

            raise ValueError('No users created. Call .prepare_users() first.')
        
        elif len(self.users) < 2:

            raise ValueError('Minimum 2 users required.')

        if self.like_count == 0 or self.dislike_count == 0 or self.like_ratio == 0:

            raise ValueError('Call .prepare_like_dislike_estimate() first.')


    @staticmethod
    def get_db_row_count():

        return {
            'users_count': get_user_model().objects.count(),
            'events_count': Events.objects.count(),
            'audio_clips_count': AudioClips.objects.count(),
            'audio_clip_likes_dislikes_count': AudioClipLikesDislikes.objects.count(),
            'event_reply_queues': EventReplyQueues.objects.count(),
            'user_events': UserEvents.objects.count(),
        }


    def prepare_new_users(self):

        user_count = 0

        if get_user_model().objects.filter(username_lowercase__startswith=self.user_prefix).exists() is True:

            latest_test_user = get_user_model().objects.filter(username_lowercase__startswith=self.user_prefix.lower()).order_by('-date_joined')[:1]
            latest_test_user = latest_test_user[0]

            print('Found latest test user: ' + latest_test_user.username)

            #if latest user is username99, we set starting count to 100 when creating new users
            user_count = int(latest_test_user.username_lowercase[len(self.user_prefix):]) + 1

        #create users

        for x in range(user_count, user_count+(self.user_quantity*self.batch_quantity)):

            new_username = self.user_prefix + str(x)
            new_email = new_username + '@gmail.com'

            self.users.append(
                get_user_model().objects.create_user(
                    username=new_username,
                    email=new_email,
                    is_active=True,
                )
            )

            print('Created test user: ' + self.users[-1].username)


    def prepare_like_dislike_estimate(self):

        if self.like_dislike_activity == 'low':

            #for every audio_clip, 0.25 users will like, 0.25 users will dislike
            self.like_count = math.ceil(len(self.users) / 4)
            self.dislike_count = math.ceil(len(self.users) / 2) - self.like_count
            self.like_ratio = (self.like_count / len(self.users)) / 100

        elif self.like_dislike_activity == 'high':

            #for every audio_clip, half users will like, half will dislike
            self.like_count = math.ceil(len(self.users) / 2)
            self.dislike_count = len(self.users) - self.like_count
            self.like_ratio = (self.like_count / len(self.users)) / 100


    def create_event_incomplete(self):

        self._check_ready()

        for audio_clip_tone_index, audio_clip_tone in enumerate(self.audio_clip_tones):

            #skip audio_clip_tone
            if audio_clip_tone_index in self.excluded_audio_clip_tones_index:

                print('Skipping excluded audio_clip_tones.')
                continue

            #events

            events = []

            for user in self.users:

                #if we only need originator, use current user
                #if we need responder, use user_index+1

                #create events, audio_clips, audio_clip_likes_dislikes
                #create extra "incomplete" events that are in the midst of replying

                for x in range(self.event_quantity):

                    events.append(
                        Events(
                            event_name=("An event by " + user.username),
                            generic_status=self.generic_statuses['incomplete'],
                            created_by=user,
                        )
                    )

            events = Events.objects.bulk_create(events, batch_size=self.bulk_create_batch_size)

            #audio_clips

            audio_clips = []

            for event in events:

                audio_clips.append(
                    AudioClips(
                        user=event.created_by,
                        audio_clip_role=self.audio_clip_roles['originator'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=self.generic_statuses['ok'],
                        audio_file=self.audio_file,
                        audio_duration_s=10,
                        like_count=self.like_count,
                        dislike_count=self.dislike_count,
                        like_ratio=self.like_ratio,
                        is_banned=False,
                    )
                )

            self.audio_clips.extend(AudioClips.objects.bulk_create(audio_clips, batch_size=self.bulk_create_batch_size))

            print('Done with audio_clip_tone #' + str(audio_clip_tone_index) + '.')


    def create_event_incomplete__is_replying(self):

        self._check_ready()

        for audio_clip_tone_index, audio_clip_tone in enumerate(self.audio_clip_tones):

            #skip audio_clip_tone
            if audio_clip_tone_index in self.excluded_audio_clip_tones_index:

                print('Skipping excluded audio_clip_tones.')
                continue

            #events

            events = []

            for user in self.users:

                #if we only need originator, use current user
                #if we need responder, use user_index+1

                #create events, audio_clips, audio_clip_likes_dislikes
                #create extra "incomplete" events that are in the midst of replying

                for x in range(self.event_quantity):

                    events.append(
                        Events(
                            event_name=("An event by " + user.username),
                            generic_status=self.generic_statuses['incomplete'],
                            created_by=user,
                        )
                    )

            events = Events.objects.bulk_create(events, batch_size=self.bulk_create_batch_size)

            #audio_clips, event_reply_queues

            audio_clips = []
            event_reply_queues = []

            when_locked = get_datetime_now() - timedelta(seconds=10)
            user_index = 0

            for event in events:

                audio_clips.append(
                    AudioClips(
                        user=event.created_by,
                        audio_clip_role=self.audio_clip_roles['originator'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=self.generic_statuses['ok'],
                        audio_file=self.audio_file,
                        audio_duration_s=10,
                        like_count=self.like_count,
                        dislike_count=self.dislike_count,
                        like_ratio=self.like_ratio,
                        is_banned=False,
                    )
                )

                try:

                    #use this statement to check for IndexError
                    #also might as well +=1 if users are the same
                    if self.users[user_index] == event.created_by.pk:

                        user_index += 1

                except IndexError:

                    #out of range, restart
                    user_index = 0

                    if self.users[user_index] == event.created_by.pk:

                        user_index += 1

                event_reply_queues.append(
                    EventReplyQueues(
                        event=event,
                        when_locked=when_locked,
                        locked_for_user=self.users[user_index],
                        is_replying=True,
                    )
                )

                user_index += 1

            self.audio_clips.extend(AudioClips.objects.bulk_create(audio_clips, batch_size=self.bulk_create_batch_size))

            EventReplyQueues.objects.bulk_create(event_reply_queues, batch_size=self.bulk_create_batch_size)

            print('Done with audio_clip_tone #' + str(audio_clip_tone_index) + '.')


    def create_event_incomplete__skipped_by_responders(self):

        #only using half of total users

        self._check_ready()

        for audio_clip_tone_index, audio_clip_tone in enumerate(self.audio_clip_tones):

            #skip audio_clip_tone
            if audio_clip_tone_index in self.excluded_audio_clip_tones_index:

                print('Skipping excluded audio_clip_tones.')
                continue

            #events

            events = []

            for user in self.users:

                #if we only need originator, use current user
                #if we need responder, use user_index+1

                #create events, audio_clips, audio_clip_likes_dislikes
                #create extra "incomplete" events that are in the midst of replying

                for x in range(self.event_quantity):

                    events.append(
                        Events(
                            event_name=("An event by " + user.username),
                            generic_status=self.generic_statuses['incomplete'],
                            created_by=user,
                        )
                    )

            events = Events.objects.bulk_create(events, batch_size=self.bulk_create_batch_size)

            #audio_clips

            audio_clips = []

            for event in events:

                audio_clips.append(
                    AudioClips(
                        user=event.created_by,
                        audio_clip_role=self.audio_clip_roles['originator'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=self.generic_statuses['ok'],
                        audio_file=self.audio_file,
                        audio_duration_s=10,
                        like_count=self.like_count,
                        dislike_count=self.dislike_count,
                        like_ratio=self.like_ratio,
                        is_banned=False,
                    )
                )

            self.audio_clips.extend(AudioClips.objects.bulk_create(audio_clips, batch_size=self.bulk_create_batch_size))

            #user_events

            user_events = []

            user_index = 0
            when_excluded_for_reply = get_datetime_now() - timedelta(seconds=10)
            user_event_quantity_per_event = math.ceil(len(self.users) / 3)

            for event in events:

                for x in range(user_event_quantity_per_event):

                    try:

                        if self.users[user_index] == event.created_by.pk:

                            user_index += 1

                    except IndexError:

                        user_index = 0

                    responder_user = self.users[user_index]
                    user_index += 1

                    user_events.append(
                        UserEvents(
                            user=responder_user,
                            event=event,
                            when_excluded_for_reply=when_excluded_for_reply,
                        )
                    )

            user_events = UserEvents.objects.bulk_create(user_events, batch_size=self.bulk_create_batch_size)

            print('Done with audio_clip_tone #' + str(audio_clip_tone_index) + '.')


    def create_event_completed(self):

        self._check_ready()

        for audio_clip_tone_index, audio_clip_tone in enumerate(self.audio_clip_tones):

            #skip audio_clip_tone
            if audio_clip_tone_index in self.excluded_audio_clip_tones_index:

                print('Skipping excluded audio_clip_tones.')
                continue

            #events

            events = []

            for user in self.users:

                #if we only need originator, use current user
                #if we need responder, use user_index+1

                #create events, audio_clips, audio_clip_likes_dislikes
                #create extra "incomplete" events that are in the midst of replying

                for x in range(self.event_quantity):

                    events.append(
                        Events(
                            event_name=("An event by " + user.username),
                            generic_status=self.generic_statuses['completed'],
                            created_by=user,
                        )
                    )

            events = Events.objects.bulk_create(events, batch_size=self.bulk_create_batch_size)

            #audio_clips

            audio_clips = []

            responder_user_index = 0

            for event in events:

                audio_clips.append(
                    AudioClips(
                        user=event.created_by,
                        audio_clip_role=self.audio_clip_roles['originator'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=self.generic_statuses['ok'],
                        audio_file=self.audio_file,
                        audio_duration_s=10,
                        like_count=self.like_count,
                        dislike_count=self.dislike_count,
                        like_ratio=self.like_ratio,
                        is_banned=False,
                    )
                )

                #for responder, we +1 self.users until the end, then restart from 0
                #originator and responder cannot be the same
                responder = None

                try:

                    #use this statement to check for IndexError
                    #also might as well +=1 if users are the same
                    if self.users[responder_user_index] == event.created_by.pk:

                        responder_user_index += 1

                except IndexError:

                    #out of range, restart
                    responder_user_index = 0

                    if self.users[responder_user_index] == event.created_by.pk:

                        responder_user_index += 1

                responder = self.users[responder_user_index]
                responder_user_index += 1

                audio_clips.append(
                    AudioClips(
                        user=responder,
                        audio_clip_role=self.audio_clip_roles['responder'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=self.generic_statuses['ok'],
                        audio_file=self.audio_file,
                        audio_duration_s=10,
                        like_count=self.like_count,
                        dislike_count=self.dislike_count,
                        like_ratio=self.like_ratio,
                        is_banned=False,
                    )
                )

            self.audio_clips.extend(AudioClips.objects.bulk_create(audio_clips, batch_size=self.bulk_create_batch_size))

            print('Done with audio_clip_tone #' + str(audio_clip_tone_index) + '.')


    def create_event_deleted__no_reply(self):

        self._check_ready()

        for audio_clip_tone_index, audio_clip_tone in enumerate(self.audio_clip_tones):

            #skip audio_clip_tone
            if audio_clip_tone_index in self.excluded_audio_clip_tones_index:

                print('Skipping excluded audio_clip_tones.')
                continue

            #events

            events = []

            for user in self.users:

                #if we only need originator, use current user
                #if we need responder, use user_index+1

                #create events, audio_clips, audio_clip_likes_dislikes
                #create extra "incomplete" events that are in the midst of replying

                for x in range(self.event_quantity):

                    events.append(
                        Events(
                            event_name=("An event by " + user.username),
                            generic_status=self.generic_statuses['deleted'],
                            created_by=user,
                        )
                    )

            events = Events.objects.bulk_create(events, batch_size=self.bulk_create_batch_size)

            #audio_clips

            audio_clips = []

            for event in events:

                audio_clips.append(
                    AudioClips(
                        user=event.created_by,
                        audio_clip_role=self.audio_clip_roles['originator'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=self.generic_statuses['deleted'],
                        audio_file=self.audio_file,
                        audio_duration_s=10,
                        like_count=self.like_count,
                        dislike_count=self.dislike_count,
                        like_ratio=self.like_ratio,
                        is_banned=False,
                    )
                )

            self.audio_clips.extend(AudioClips.objects.bulk_create(audio_clips, batch_size=self.bulk_create_batch_size))

            print('Done with audio_clip_tone #' + str(audio_clip_tone_index) + '.')


    def create_event_deleted__has_reply(self):

        self._check_ready()

        #we save the highest quantity of rows for execution outside of loop
        #this is so when rows are very few, we can at least speed things up this way
        #can't do it for things like AudioClips because they must first exist before AudioClipLikesDislikes can exist
        audio_clip_likes_dislikes = []

        for audio_clip_tone_index, audio_clip_tone in enumerate(self.audio_clip_tones):

            #skip audio_clip_tone
            if audio_clip_tone_index in self.excluded_audio_clip_tones_index:

                print('Skipping excluded audio_clip_tones.')
                continue

            #events

            events = []

            for user in self.users:

                #if we only need originator, use current user
                #if we need responder, use user_index+1

                #create events, audio_clips, audio_clip_likes_dislikes
                #create extra "incomplete" events that are in the midst of replying

                for x in range(self.event_quantity):

                    events.append(
                        Events(
                            event_name=("An event by " + user.username),
                            generic_status=self.generic_statuses['deleted'],
                            created_by=user,
                        )
                    )

            events = Events.objects.bulk_create(events, batch_size=self.bulk_create_batch_size)

            #audio_clips

            audio_clips = []

            responder_user_index = 0

            for event in events:

                audio_clips.append(
                    AudioClips(
                        user=event.created_by,
                        audio_clip_role=self.audio_clip_roles['originator'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=self.generic_statuses['deleted'],
                        audio_file=self.audio_file,
                        audio_duration_s=10,
                        like_count=self.like_count,
                        dislike_count=self.dislike_count,
                        like_ratio=self.like_ratio,
                        is_banned=True,
                    )
                )

                #for responder, we +1 self.users until the end, then restart from 0
                #originator and responder cannot be the same
                responder = None

                try:

                    #use this statement to check for IndexError
                    #also might as well +=1 if users are the same
                    if self.users[responder_user_index] == event.created_by.pk:

                        responder_user_index += 1

                except IndexError:

                    #out of range, restart
                    responder_user_index = 0

                    if self.users[responder_user_index] == event.created_by.pk:

                        responder_user_index += 1

                responder = self.users[responder_user_index]
                responder_user_index += 1

                audio_clips.append(
                    AudioClips(
                        user=responder,
                        audio_clip_role=self.audio_clip_roles['responder'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=self.generic_statuses['ok'],
                        audio_file=self.audio_file,
                        audio_duration_s=10,
                        like_count=self.like_count,
                        dislike_count=self.dislike_count,
                        like_ratio=self.like_ratio,
                        is_banned=False,
                    )
                )

            self.audio_clips.extend(AudioClips.objects.bulk_create(audio_clips, batch_size=self.bulk_create_batch_size))

            print('Done with audio_clip_tone #' + str(audio_clip_tone_index) + '.')


    def create_audio_clip_likes_dislikes(self):

        #likes dislikes

        audio_clip_likes_dislikes = []

        if self.like_dislike_activity == 'low':

            user_index = 0

            for audio_clip in self.audio_clips:

                current_like_count = 0
                current_dislike_count = 0
                current_user = None

                #likes
                while current_like_count < self.like_count:

                    try:

                        current_user = self.users[user_index]

                    except IndexError:

                        user_index = 0
                        current_user = self.users[user_index]

                    audio_clip_likes_dislikes.append(
                        AudioClipLikesDislikes(
                            user=current_user,
                            audio_clip=audio_clip,
                            is_liked=True
                        )
                    )

                    user_index += 1
                    current_like_count += 1

                #dislikes
                while current_like_count < self.dislike_count:

                    try:

                        current_user = self.users[user_index]

                    except IndexError:

                        user_index = 0
                        current_user = self.users[user_index]

                    audio_clip_likes_dislikes.append(
                        AudioClipLikesDislikes(
                            user=self.users[user_index],
                            audio_clip=audio_clip,
                            is_liked=False
                        )
                    )

                    user_index += 1
                    current_dislike_count += 1

        elif self.like_dislike_activity == 'high':

            for audio_clip in self.audio_clips:

                #50% users will like
                for x in range(0, self.like_count):

                    audio_clip_likes_dislikes.append(
                        AudioClipLikesDislikes(
                            user=self.users[x],
                            audio_clip=audio_clip,
                            is_liked=True
                        )
                    )

                #50% users will dislike
                for x in range(self.like_count, len(self.users)):

                    audio_clip_likes_dislikes.append(
                        AudioClipLikesDislikes(
                            user=self.users[x],
                            audio_clip=audio_clip,
                            is_liked=False
                        )
                    )

        #since this has the highest quantity, we can run it as one .bulk_create()
        print('Running .bulk_create() with ' + str(len(audio_clip_likes_dislikes)) + ' items for audio_clip_likes_dislikes.')
        audio_clip_likes_dislikes = AudioClipLikesDislikes.objects.bulk_create(audio_clip_likes_dislikes, batch_size=self.bulk_create_batch_size)



@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    DEBUG=True,
)
class RealisticBulkData_TestCase(TestCase):

    #{test_function_name: anything}
    metrics = {}

    @classmethod
    def setUpTestData(cls):

        pass


    @classmethod
    def tearDownClass(cls):

        #print more beautifully
        for function_name in cls.metrics:

            print(function_name)
            print(cls.metrics[function_name])
            print('\n')

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


    def test_realistic_bulk_data__event_incomplete(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_incomplete()
        realistic_bulk_data_class.create_audio_clip_likes_dislikes()
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })


    def test_realistic_bulk_data__event_incomplete__is_replying(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_incomplete__is_replying()
        realistic_bulk_data_class.create_audio_clip_likes_dislikes()
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })


    def test_realistic_bulk_data__event_incomplete__skipped_by_responders(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_incomplete__skipped_by_responders()
        realistic_bulk_data_class.create_audio_clip_likes_dislikes()
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })


    def test_realistic_bulk_data__event_completed(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_completed()
        realistic_bulk_data_class.create_audio_clip_likes_dislikes()
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })


    def test_realistic_bulk_data__event_deleted_no_reply(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_deleted__no_reply()
        realistic_bulk_data_class.create_audio_clip_likes_dislikes()
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })


    def test_realistic_bulk_data__event_deleted_has_reply(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_deleted__has_reply()
        realistic_bulk_data_class.create_audio_clip_likes_dislikes()
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })



#since we have cursor tokens, always test (latest->back/to), (earliest->back/to)
#can we inherit this class and do high bulk_quantity for RealisticBulkData()?
#specify --keepdb when running tests to only run bulk data creation once
@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    DEBUG=True,
)
class Core_TestCase(TestCase):

    #{test_function_name: anything}
    metrics = {}

    @classmethod
    def setUpTestData(cls):

        cls.realistic_bulk_data_class = RealisticBulkData()

        if AudioClips.objects.count() == 0:

            cls.realistic_bulk_data_class.prepare_new_users()
            cls.realistic_bulk_data_class.prepare_like_dislike_estimate()
            # cls.realistic_bulk_data_class.create_event_incomplete()
            cls.realistic_bulk_data_class.create_event_completed()
            cls.realistic_bulk_data_class.create_audio_clip_likes_dislikes()

        cls.metrics.update({'all_rows': cls.realistic_bulk_data_class.get_db_row_count()})


    @classmethod
    def tearDownClass(cls):

        #print more beautifully
        for function_name in cls.metrics:

            print(function_name)
            print(cls.metrics[function_name])
            print('\n')

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


    def test_browse_events__latest__all(self):

        self.login(self.realistic_bulk_data_class.users[0])

        metrics = {}
        stopwatch = Stopwatch()

        #it is difficult to write easy queries here to take cursor tokens into account
        #take 2x rows with simpler query to test cursor tokens later
        expected_rows = AudioClips.objects.filter(
            audio_clip_role__audio_clip_role_name='originator',
        ).order_by('-when_created', '-id')[0:settings.EVENT_QUANTITY_PER_PAGE*2]

        #basic, next

        data = {
            'latest_or_best': 'latest',
            'timeframe': 'all',
            'audio_clip_role_name': 'originator',
            'next_or_back': 'next',
        }

        stopwatch.start()

        request = self.client.get(
            reverse(
                'browse_events_api',
                kwargs=data
            )
        )
        self.assertEqual(request.status_code, 200)

        stopwatch.end()

        metrics.update({
            'next__no_token': {
                'data': data,
                'time_s': stopwatch.diff_seconds(),
            }
        })

        #check

        #next_token, back_token, data
        response_data = get_response_data(request)

        #[{event:event,originator:[],responder:[]}]
        for x in range(0, settings.EVENT_QUANTITY_PER_PAGE):

            self.assertEqual(expected_rows[x].pk, response_data['data'][x]['originator'][0]['id'])

        #basic+token, next

        data = {
            'latest_or_best': 'latest',
            'timeframe': 'all',
            'audio_clip_role_name': 'originator',
            'next_or_back': 'next',
            'cursor_token': response_data['next_token']
        }

        stopwatch.start()

        request = self.client.get(
            reverse(
                'browse_events_api',
                kwargs=data
            )
        )
        self.assertEqual(request.status_code, 200)

        stopwatch.end()

        metrics.update({
            'next_token': {
                'data': data,
                'time_s': stopwatch.diff_seconds(),
            }
        })

        #check

        #next_token, back_token, data
        response_data = get_response_data(request)

        #[{event:event,originator:[],responder:[]}]
        for x in range(settings.EVENT_QUANTITY_PER_PAGE, settings.EVENT_QUANTITY_PER_PAGE * 2):

            self.assertEqual(expected_rows[x].pk, response_data['data'][x - settings.EVENT_QUANTITY_PER_PAGE]['originator'][0]['id'])

        #basic+token, back

        data = {
            'latest_or_best': 'latest',
            'timeframe': 'all',
            'audio_clip_role_name': 'originator',
            'next_or_back': 'back',
            'cursor_token': response_data['back_token']
        }

        stopwatch.start()

        request = self.client.get(
            reverse(
                'browse_events_api',
                kwargs=data
            )
        )
        self.assertEqual(request.status_code, 200)

        stopwatch.end()

        metrics.update({
            'back_token': {
                'data': data,
                'time_s': stopwatch.diff_seconds(),
            }
        })

        #check

        #next_token, back_token, data
        response_data = get_response_data(request)

        #[{event:event,originator:[],responder:[]}]
        for x in range(0, settings.EVENT_QUANTITY_PER_PAGE):

            self.assertEqual(expected_rows[x].pk, response_data['data'][x]['originator'][0]['id'])

        #basic+back, expect no rows

        data = {
            'latest_or_best': 'latest',
            'timeframe': 'all',
            'audio_clip_role_name': 'originator',
            'next_or_back': 'back',
            'cursor_token': response_data['back_token']
        }

        stopwatch.start()

        request = self.client.get(
            reverse(
                'browse_events_api',
                kwargs=data
            )
        )
        self.assertEqual(request.status_code, 200)

        stopwatch.end()

        metrics.update({
            'back_token__no_rows': {
                'data': data,
                'time_s': stopwatch.diff_seconds(),
            }
        })

        #check

        #next_token, back_token, data
        response_data = get_response_data(request)

        self.assertEqual(len(response_data['data']), 0)

        #all done

        self.metrics.update({inspect.currentframe().f_code.co_name: metrics})


    def test_browse_events__latest__by_audio_clip_tone(self):

        pass


    def test_browse_events__latest__by_unused_audio_clip_tone(self):

        pass


    def test_browse_events__user_latest__all(self):

        pass


    def test_browse_events__user_latest__by_audio_clip_tone(self):

        pass


    def test_browse_events__user_latest__by_unused_audio_clip_tone(self):

        pass


    def test_browse_events__user_latest_likes_dislikes__all(self):

        pass


    def test_browse_events__user_latest_likes_dislikes__by_audio_clip_tone(self):

        pass


    def test_browse_events__user_latest_likes_dislikes__by_unused_audio_clip_tone(self):

        pass


    def test_list_event_reply_choices__ok(self):

        pass


    def test_list_event_reply_choices__no_events(self):

        pass


    def test_list_event_reply_choices__many_skipped(self):

        pass


















