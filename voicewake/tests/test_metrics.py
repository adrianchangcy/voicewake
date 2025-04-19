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
import threading



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
#trying out suggestions to optimise this:
    #using positional args (id, user)(None, current_user.id) instead of kwargs for models
    #using DEBUG=False at settings.dev
class RealisticBulkData():

    def __init__(
        self,
        batch_quantity=1,
        is_audio_clip_tone_quantity_reduced=True,
        db_batch_size=500,
    ):

        self.batch_quantity = batch_quantity
        self.is_audio_clip_tone_quantity_reduced = is_audio_clip_tone_quantity_reduced
        self.db_batch_size = db_batch_size

        self.user_quantity = 10 * batch_quantity
        self.user_prefix = "testuser"
        self.user_count = 0
        self.users = []
        self.audio_file = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/audio_ok_1.mp3'
        )

        #keep this lower so you can frequently mix and match the creating phase for more realistic data
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

        self.audio_clip_tones = []

        if self.is_audio_clip_tone_quantity_reduced is True:

            new_audio_clip_tone_quantity = math.ceil(AudioClipTones.objects.count() / 4)
            self.audio_clip_tones = AudioClipTones.objects.all()[:new_audio_clip_tone_quantity]

        else:

            self.audio_clip_tones = AudioClipTones.objects.all()

        self.excluded_audio_clip_tones_indexes = []

        audio_clip_tones_per_quarter = math.floor(len(self.audio_clip_tones) / 4)

        #closest to start, but not first
        self.excluded_audio_clip_tones_indexes.append(1)
        #second quarter
        self.excluded_audio_clip_tones_indexes.append((audio_clip_tones_per_quarter*2) - 1)
        #third quarter
        self.excluded_audio_clip_tones_indexes.append((audio_clip_tones_per_quarter*3) - 1)
        #closest to end, but not last
        self.excluded_audio_clip_tones_indexes.append(len(self.audio_clip_tones) - 2)

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

        for x in range(user_count, user_count+self.user_quantity):

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

        if self.user_quantity < 10:

            raise ValueError('To keep things simple, please maintain a minimum of 10.')

        if len(self.users) == 0:

            raise ValueError('No users. Call .prepare_new_users() first.')

        #to prevent full exponential scaling, allow an amount of users to not vote at every audio_clip

        #len(users) must not be divisible by (like_count + dislike_count), else one user has only likes, the other dislikes, etc.
        #this is easily achieved by doing (len(users)/2)+1
        #better +1 than -1, since having too few also means some users have only likes/dislikes
        self.like_count = math.ceil(len(self.users) * 0.25)
        self.dislike_count = math.ceil(len(self.users) * 0.5) + 1

        self.like_ratio = (self.like_count / (self.like_count + self.dislike_count)) / 100


    #initially though only running this once for all create() is more efficient
    #but that doesn't help when everything is too slow, so this will be coupled into all individual create(), then use threading to execute
    def _create_audio_clip_likes_dislikes(self, audio_clips):

        #likes dislikes
        #len(users) must not be divisible by (like_count + dislike_count), else one user has only likes, the other dislikes, etc.

        datetime_now = get_datetime_now()

        audio_clip_likes_dislikes = []

        user_index = 0

        for audio_clip in audio_clips:

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
                        None,
                        current_user.id,
                        audio_clip.id,
                        True,
                        datetime_now,
                        datetime_now,
                    )
                )

                user_index += 1
                current_like_count += 1

            #dislikes
            while current_dislike_count < self.dislike_count:

                try:

                    current_user = self.users[user_index]

                except IndexError:

                    user_index = 0
                    current_user = self.users[user_index]

                audio_clip_likes_dislikes.append(
                    AudioClipLikesDislikes(
                        None,
                        current_user.id,
                        audio_clip.id,
                        False,
                        datetime_now,
                        datetime_now,
                    )
                )

                user_index += 1
                current_dislike_count += 1

        audio_clip_likes_dislikes = AudioClipLikesDislikes.objects.bulk_create(audio_clip_likes_dislikes, batch_size=self.db_batch_size)


    def create_event_incomplete(self, is_replying:bool=False, skipped_by_users:bool=False):

        self._check_ready()

        print_with_function_name(f"Started. is_replying={str(is_replying)}, skipped_by_users={str(skipped_by_users)}.")

        datetime_now = get_datetime_now()

        for audio_clip_tone_index, audio_clip_tone in enumerate(self.audio_clip_tones):

            #skip audio_clip_tone
            if audio_clip_tone_index in self.excluded_audio_clip_tones_indexes:

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
                            None,
                            "An event by " + user.username,
                            self.generic_statuses['incomplete'].id,
                            user.id,
                            datetime_now,
                            datetime_now,
                        )
                    )

            events = Events.objects.bulk_create(events, batch_size=self.db_batch_size)

            #audio_clips, event_reply_queues, user_events

            audio_clips = []
            event_reply_queues = []
            user_events = []

            replying_user_index = 0
            when_locked = get_datetime_now() - timedelta(seconds=10)
            when_excluded_for_reply = get_datetime_now() - timedelta(seconds=20)

            for event in events:

                audio_clips.append(
                    AudioClips(
                        None,
                        event.created_by.id,
                        self.audio_clip_roles['originator'].id,
                        audio_clip_tone.id,
                        event.id,
                        self.generic_statuses['ok'].id,
                        self.audio_file,
                        10,
                        [],
                        self.like_count,
                        self.dislike_count,
                        self.like_ratio,
                        False,
                        datetime_now,
                        datetime_now,
                    )
                )

                #event_reply_queues

                if is_replying is True:

                    try:

                        #use this statement to check for IndexError
                        #also might as well +=1 if users are the same
                        if self.users[replying_user_index] == event.created_by.pk:

                            replying_user_index += 1

                    except IndexError:

                        #out of range, restart
                        replying_user_index = 0

                        if self.users[replying_user_index] == event.created_by.pk:

                            replying_user_index += 1

                    event_reply_queues.append(
                        EventReplyQueues(
                            None,
                            event.id,
                            when_locked,
                            self.users[replying_user_index].id,
                            True,
                            datetime_now,
                            datetime_now,
                        )
                    )

                #users who have skipped before
                #we refer to existing user in event_reply_queues if is_replying=True, so we don't have the same user skipping and replying

                if skipped_by_users is True:

                    for user in self.users:

                        if is_replying is True and self.users[replying_user_index].id == user.id:

                            continue

                        user_events.append(
                            UserEvents(
                                None,
                                user.id,
                                event.id,
                                when_excluded_for_reply,
                                when_excluded_for_reply,
                            )
                        )

                replying_user_index += 1


            audio_clips = AudioClips.objects.bulk_create(audio_clips, batch_size=self.db_batch_size)

            if is_replying is True:

                event_reply_queues = EventReplyQueues.objects.bulk_create(event_reply_queues, batch_size=self.db_batch_size)

            if skipped_by_users is True:

                user_events = UserEvents.objects.bulk_create(user_events, batch_size=self.db_batch_size)

            self._create_audio_clip_likes_dislikes(audio_clips)

            print('Done with audio_clip_tone #' + str(audio_clip_tone_index) + '.')


    def create_event_completed(self):

        self._check_ready()

        print_with_function_name(f"Started.")

        datetime_now = get_datetime_now()

        for audio_clip_tone_index, audio_clip_tone in enumerate(self.audio_clip_tones):

            #skip audio_clip_tone
            if audio_clip_tone_index in self.excluded_audio_clip_tones_indexes:

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
                            None,
                            "An event by " + user.username,
                            self.generic_statuses['completed'].id,
                            user.id,
                            datetime_now,
                            datetime_now,
                        )
                    )

            events = Events.objects.bulk_create(events, batch_size=self.db_batch_size)

            #audio_clips

            audio_clips = []

            responder_user_index = 0

            for event in events:

                audio_clips.append(
                    AudioClips(
                        None,
                        event.created_by.id,
                        self.audio_clip_roles['originator'].id,
                        audio_clip_tone.id,
                        event.id,
                        self.generic_statuses['ok'].id,
                        self.audio_file,
                        10,
                        [],
                        self.like_count,
                        self.dislike_count,
                        self.like_ratio,
                        False,
                        datetime_now,
                        datetime_now,
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
                        None,
                        responder.id,
                        self.audio_clip_roles['responder'].id,
                        audio_clip_tone.id,
                        event.id,
                        self.generic_statuses['ok'].id,
                        self.audio_file,
                        10,
                        [],
                        self.like_count,
                        self.dislike_count,
                        self.like_ratio,
                        False,
                        datetime_now,
                        datetime_now,
                    )
                )

            audio_clips = AudioClips.objects.bulk_create(audio_clips, batch_size=self.db_batch_size)
            self._create_audio_clip_likes_dislikes(audio_clips)

            print('Done with audio_clip_tone #' + str(audio_clip_tone_index) + '.')


    def create_event_deleted(self, has_reply:bool=False, deleted_and_banned:bool=False):

        self._check_ready()

        print_with_function_name(f"Started. has_reply={str(has_reply)}, deleted_and_banned={str(deleted_and_banned)}.")

        datetime_now = get_datetime_now()

        for audio_clip_tone_index, audio_clip_tone in enumerate(self.audio_clip_tones):

            #skip audio_clip_tone
            if audio_clip_tone_index in self.excluded_audio_clip_tones_indexes:

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
                            None,
                            "An event by " + user.username,
                            self.generic_statuses['deleted'].id,
                            user.id,
                            datetime_now,
                            datetime_now,
                        )
                    )

            events = Events.objects.bulk_create(events, batch_size=self.db_batch_size)

            #audio_clips

            audio_clips = []

            responder_user_index = 0

            for event in events:

                audio_clips.append(
                    AudioClips(
                        None,
                        event.created_by.id,
                        self.audio_clip_roles['originator'].id,
                        audio_clip_tone.id,
                        event.id,
                        self.generic_statuses['deleted'].id,
                        self.audio_file,
                        10,
                        [],
                        self.like_count,
                        self.dislike_count,
                        self.like_ratio,
                        deleted_and_banned,
                        datetime_now,
                        datetime_now,
                    )
                )

                if has_reply is False:

                    continue

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
                        None,
                        responder.id,
                        self.audio_clip_roles['responder'].id,
                        audio_clip_tone.id,
                        event.id,
                        self.generic_statuses['ok'].id,
                        self.audio_file,
                        10,
                        [],
                        self.like_count,
                        self.dislike_count,
                        self.like_ratio,
                        False,
                        datetime_now,
                        datetime_now,
                    )
                )


            audio_clips = AudioClips.objects.bulk_create(audio_clips, batch_size=self.db_batch_size)
            self._create_audio_clip_likes_dislikes(audio_clips)

            print('Done with audio_clip_tone #' + str(audio_clip_tone_index) + '.')


    @staticmethod
    def sample_run():

        #cmd:
            #python manage.py shell -c "from voicewake.tests.test_metrics import RealisticBulkData; RealisticBulkData.sample_run();"

        realistic_bulk_data_class = RealisticBulkData(batch_quantity=10, is_audio_clip_tone_quantity_reduced=False, db_batch_size=100)

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()

        #this improves realism of randomness
        max_randomness_iteration_count = 3
        current_randomness_iteration_count = 0

        while current_randomness_iteration_count < max_randomness_iteration_count:

            threads = []

            threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_incomplete, args=(True, False)))
            threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_incomplete, args=(False, True)))
            threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_incomplete, args=(True, True)))
            threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_incomplete, args=(False, False)))

            threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_completed))

            threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_deleted, args=(True, False)))
            threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_deleted, args=(False, True)))
            threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_deleted, args=(True, True)))
            threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_deleted, args=(False, False)))

            random.shuffle(threads)

            #run 2 threads at a time

            thread_index = 0

            while thread_index < len(threads):

                is_last_thread = False

                #start threads

                threads[thread_index].start()

                try:

                    threads[thread_index+1].start()

                except IndexError:

                    is_last_thread = True

                #pause main thread until done

                threads[thread_index].join()

                if is_last_thread is False:

                    threads[thread_index+1].join()
                    thread_index += 2

                else:

                    thread_index += 1

            current_randomness_iteration_count += 1











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


    @staticmethod
    def check_likes_dislikes_of_users(realistic_bulk_data_class:RealisticBulkData):

        print('\n\n')
        print(realistic_bulk_data_class.like_count)
        print(realistic_bulk_data_class.dislike_count)
        print(realistic_bulk_data_class.like_ratio)
        print(AudioClipLikesDislikes.objects.filter(is_liked=True).count())
        print(AudioClipLikesDislikes.objects.filter(is_liked=False).count())
        for user in realistic_bulk_data_class.users:
            print(user.username)
            print(AudioClipLikesDislikes.objects.filter(user=user, is_liked=True).count())
            print(AudioClipLikesDislikes.objects.filter(user=user, is_liked=False).count())


    def test_realistic_bulk_data__event_incomplete(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_incomplete()
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })


    def test_realistic_bulk_data__event_incomplete__is_replying(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_incomplete(is_replying=True)
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })


    def test_realistic_bulk_data__event_incomplete__skipped_by_responders(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_incomplete(skipped_by_users=True)
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })


    def test_realistic_bulk_data__event_incomplete__all_true(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_incomplete(is_replying=True, skipped_by_users=True)
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })


    def test_realistic_bulk_data__event_completed(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_completed()
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })


    def test_realistic_bulk_data__event_deleted_no_reply(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_deleted(has_reply=False, deleted_and_banned=False)
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })


    def test_realistic_bulk_data__event_deleted_has_reply(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.prepare_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()
        realistic_bulk_data_class.create_event_deleted(has_reply=True, deleted_and_banned=False)
        self.metrics.update({
            inspect.currentframe().f_code.co_name: realistic_bulk_data_class.get_db_row_count()
        })



#since we have cursor tokens, always test (latest->back/to), (earliest->back/to)
#for tests that test on filtering, we iterate through list of filters in a single test case, else exponential
    #a test case for filters then becomes unique by differentiating into latest/earliest/empty rows to test db indexing
#you may see a repeat queryset between audio_clip_tone_id and expected_rows
    #this is necessary so we can do [:1] and guarantee all expected_rows later only has the same audio_clip_tone
    #expected_rows on its own cannot guarantee that all rows have the same audio_clip_tone
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
        raise ValueError('Figure out how to make this test class use specified db')
        #also, update everything related to "self.realistic_bulk_data_class" in this test class

        cls.metrics.update({'all_rows': RealisticBulkData.get_db_row_count()})


    @classmethod
    def tearDownClass(cls):

        print('\n\n\n\n\n')

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


    def test_browse_events__no_audio_clip_tone(self):

        logged_in_user = self.realistic_bulk_data_class.users[0]
        metrics = {}
        stopwatch = Stopwatch()

        self.login(logged_in_user)

        #==========
        #main page, only completed
        #==========

        latest_completed_kwargs = []
        latest_completed_expected_rows = []
        latest_completed_audio_clip_tone_ids = []

        #no tone
        for audio_clip_role_name in ['originator', 'responder']:
            audio_clip_tone_id = None
            latest_completed_audio_clip_tone_ids.append(None)
            latest_completed_kwargs.append({
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': audio_clip_role_name,
                'next_or_back': 'next',
            })
            latest_completed_expected_rows.append(
                AudioClips.objects.filter(
                    audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    event__generic_status__generic_status_name='completed',
                ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
            )

        #check test setup

        self.assertEqual(len(latest_completed_kwargs), len(latest_completed_audio_clip_tone_ids))
        self.assertEqual(len(latest_completed_kwargs), len(latest_completed_expected_rows))

        for expected_rows in latest_completed_expected_rows:

            self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

        #==========
        #user page, only completed
        #==========

        user_latest_completed_kwargs = []
        user_latest_completed_expected_rows = []
        user_latest_completed_audio_clip_tone_ids = []

        #no tone, user
        for audio_clip_role_name in ['originator', 'responder']:
            audio_clip_tone_id = None
            user_latest_completed_audio_clip_tone_ids.append(None)
            user_latest_completed_kwargs.append({
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': audio_clip_role_name,
                'next_or_back': 'next',
                'username': logged_in_user.username,
            })
            user_latest_completed_expected_rows.append(
                AudioClips.objects.filter(
                    audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    event__generic_status__generic_status_name='completed',
                    user=logged_in_user,
                ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
            )

        #check test setup

        self.assertEqual(len(user_latest_completed_kwargs), len(user_latest_completed_audio_clip_tone_ids))
        self.assertEqual(len(user_latest_completed_kwargs), len(user_latest_completed_expected_rows))

        for expected_rows in user_latest_completed_expected_rows:

            self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

        #==========
        #own page, latest completed, likes dislikes
        #==========

        own_latest_completed_kwargs = []
        own_latest_completed_expected_rows = []
        own_latest_completed_audio_clip_tone_ids = []

        #no tone, user, like/dislike
        for audio_clip_role_name in ['originator', 'responder']:
            event_generic_status_names = []
            if audio_clip_role_name == 'originator':
                event_generic_status_names = ['incomplete', 'completed', 'deleted']
            else:
                event_generic_status_names = ['completed', 'deleted']
            for likes_or_dislikes_choice in ['likes', 'dislikes']:
                audio_clip_tone_id = None
                own_latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
                own_latest_completed_kwargs.append({
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': audio_clip_role_name,
                    'next_or_back': 'next',
                    'likes_or_dislikes': likes_or_dislikes_choice,
                    'username': logged_in_user.username,
                })
                like_dislike_rows = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                    user=logged_in_user,
                    audio_clip__event__generic_status__generic_status_name__in=event_generic_status_names,
                    audio_clip__generic_status__generic_status_name='ok',
                    audio_clip__audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    is_liked=(likes_or_dislikes_choice == 'likes'),
                ).order_by('-last_modified', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2]
                expected_rows = []
                for row in like_dislike_rows:
                    expected_rows.append(row.audio_clip)
                own_latest_completed_expected_rows.append(expected_rows)

        #check test setup

        self.assertEqual(len(own_latest_completed_kwargs), len(own_latest_completed_audio_clip_tone_ids))
        self.assertEqual(len(own_latest_completed_kwargs), len(own_latest_completed_expected_rows))

        for expected_rows in own_latest_completed_expected_rows:

            self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

        #start

        all_kwargs = latest_completed_kwargs + user_latest_completed_kwargs + own_latest_completed_kwargs
        all_expected_rows = latest_completed_expected_rows + user_latest_completed_expected_rows + own_latest_completed_expected_rows

        for x in range(len(all_kwargs)):

            loop_title = 'loop #' + str(x)

            print(loop_title)

            #next

            stopwatch.start()

            current_kwargs:dict = all_kwargs[x].copy()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=current_kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + '__next__no_token': {
                    'data': current_kwargs.copy(),
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertGreater(len(response_data['data']), 0)

            #[{event:event,originator:[],responder:[]}]
            for xx in range(0, settings.EVENT_QUANTITY_PER_PAGE):

                self.assertEqual(
                    all_expected_rows[x][xx].pk,
                    response_data['data'][xx][all_kwargs[x]['audio_clip_role_name']][0]['id']
                )

            #next+token

            current_kwargs.update({
                'cursor_token': response_data['next_token'],
            })

            stopwatch.start()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=current_kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + '__next_token': {
                    'data': current_kwargs.copy(),
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertGreater(len(response_data['data']), 0)

            #[{event:event,originator:[],responder:[]}]
            for xx in range(settings.EVENT_QUANTITY_PER_PAGE, settings.EVENT_QUANTITY_PER_PAGE * 2):

                self.assertEqual(
                    all_expected_rows[x][xx].pk,
                    response_data['data'][xx - settings.EVENT_QUANTITY_PER_PAGE][all_kwargs[x]['audio_clip_role_name']][0]['id']
                )

            #back+token

            current_kwargs.update({
                'next_or_back': 'back',
                'cursor_token': response_data['back_token'],
            })

            stopwatch.start()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=current_kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + '__back_token': {
                    'data': current_kwargs.copy(),
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertGreater(len(response_data['data']), 0)

            #[{event:event,originator:[],responder:[]}]
            for xx in range(0, settings.EVENT_QUANTITY_PER_PAGE):

                self.assertEqual(
                    all_expected_rows[x][xx].pk,
                    response_data['data'][xx][all_kwargs[x]['audio_clip_role_name']][0]['id'])

            #back+token again, expect no rows

            current_kwargs.update({
                'next_or_back': 'back',
                'cursor_token': response_data['back_token'],
            })

            stopwatch.start()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=current_kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + '__back_token__no_rows': {
                    'data': current_kwargs.copy(),
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertEqual(len(response_data['data']), 0)

        #done

        self.metrics.update({inspect.currentframe().f_code.co_name: metrics})


    def test_browse_events__latest_used_audio_clip_tone(self):

        logged_in_user = self.realistic_bulk_data_class.users[0]
        metrics = {}
        stopwatch = Stopwatch()

        self.login(logged_in_user)

        #==========
        #main page, only completed
        #==========

        latest_completed_kwargs = []
        latest_completed_expected_rows = []
        latest_completed_audio_clip_tone_ids = []

        #has tone
        for audio_clip_role_name in ['originator', 'responder']:
            target_row = AudioClips.objects.filter(
                audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                event__generic_status__generic_status_name='completed'
            ).order_by('-when_created', '-id')[:1]
            audio_clip_tone_id = target_row.audio_clip_tone.id
            latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
            latest_completed_kwargs.append({
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': audio_clip_role_name,
                'next_or_back': 'next',
                'audio_clip_tone_id': audio_clip_tone_id,
            })
            latest_completed_expected_rows.append(
                AudioClips.objects.filter(
                    audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    event__generic_status__generic_status_name='completed',
                    audio_clip_tone__id=audio_clip_tone_id,
                ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
            )

        #check test setup

        self.assertEqual(len(latest_completed_kwargs), len(latest_completed_audio_clip_tone_ids))
        self.assertEqual(len(latest_completed_kwargs), len(latest_completed_expected_rows))

        for expected_rows in latest_completed_expected_rows:

            self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

        #==========
        #user page, only completed
        #==========

        user_latest_completed_kwargs = []
        user_latest_completed_expected_rows = []
        user_latest_completed_audio_clip_tone_ids = []

        #has tone, username
        for audio_clip_role_name in ['originator', 'responder']:
            target_row = AudioClips.objects.filter(
                audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                event__generic_status__generic_status_name='completed',
                user__id=logged_in_user.id,
            ).order_by('-when_created', '-id')[:1]
            audio_clip_tone_id = target_row.audio_clip_tone.id
            user_latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
            user_latest_completed_kwargs.append({
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': audio_clip_role_name,
                'next_or_back': 'next',
                'audio_clip_tone_id': audio_clip_tone_id,
                'username': logged_in_user.username,
            })
            user_latest_completed_expected_rows.append(
                AudioClips.objects.filter(
                    audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    event__generic_status__generic_status_name='completed',
                    audio_clip_tone__id=audio_clip_tone_id,
                    user__id=logged_in_user.id,
                ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
            )

        #check test setup

        self.assertEqual(len(user_latest_completed_kwargs), len(user_latest_completed_audio_clip_tone_ids))
        self.assertEqual(len(user_latest_completed_kwargs), len(user_latest_completed_expected_rows))

        for expected_rows in user_latest_completed_expected_rows:

            self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

        #==========
        #own page, latest completed, likes dislikes
        #==========

        own_latest_completed_kwargs = []
        own_latest_completed_expected_rows = []
        own_latest_completed_audio_clip_tone_ids = []

        #has tone, username, likes/dislikes
        for audio_clip_role_name in ['originator', 'responder']:
            event_generic_status_names = []
            if audio_clip_role_name == 'originator':
                event_generic_status_names = ['incomplete', 'completed', 'deleted']
            else:
                event_generic_status_names = ['completed', 'deleted']
            for likes_or_dislikes_choice in ['likes', 'dislikes']:
                target_row = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                    user=logged_in_user,
                    audio_clip__event__generic_status__generic_status_name__in=event_generic_status_names,
                    audio_clip__generic_status__generic_status_name='ok',
                    audio_clip__audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    is_liked=(likes_or_dislikes_choice == 'likes'),
                ).order_by('-last_modified', '-id')[:1]
                audio_clip_tone_id = target_row.audio_clip.audio_clip_tone.id
                own_latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
                own_latest_completed_kwargs.append({
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': audio_clip_role_name,
                    'next_or_back': 'next',
                    'username': logged_in_user.username,
                    'likes_or_dislikes': likes_or_dislikes_choice,
                    'audio_clip_tone_id': audio_clip_tone_id,
                })
                like_dislike_rows = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                    user=logged_in_user,
                    audio_clip__event__generic_status__generic_status_name__in=event_generic_status_names,
                    audio_clip__generic_status__generic_status_name='ok',
                    audio_clip__audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    is_liked=(likes_or_dislikes_choice == 'likes'),
                    audio_clip__audio_clip_tone__id=audio_clip_tone_id,
                ).order_by('-last_modified', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2]
                expected_rows = []
                for row in like_dislike_rows:
                    expected_rows.append(row.audio_clip)
                own_latest_completed_expected_rows.append(expected_rows)

        #check test setup

        self.assertEqual(len(own_latest_completed_kwargs), len(own_latest_completed_audio_clip_tone_ids))
        self.assertEqual(len(own_latest_completed_kwargs), len(own_latest_completed_expected_rows))

        for expected_rows in own_latest_completed_expected_rows:

            self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

        #start

        all_kwargs = latest_completed_kwargs + user_latest_completed_kwargs + own_latest_completed_kwargs
        all_expected_rows = latest_completed_expected_rows + user_latest_completed_expected_rows + own_latest_completed_expected_rows

        for x in range(len(all_kwargs)):

            loop_title = 'loop #' + str(x)

            print(loop_title)

            #next

            stopwatch.start()

            current_kwargs:dict = all_kwargs[x].copy()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=current_kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + '__next__no_token': {
                    'data': current_kwargs.copy(),
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertGreater(len(response_data['data']), 0)

            #[{event:event,originator:[],responder:[]}]
            for xx in range(0, settings.EVENT_QUANTITY_PER_PAGE):

                self.assertEqual(
                    all_expected_rows[x][xx].pk,
                    response_data['data'][xx][all_kwargs[x]['audio_clip_role_name']][0]['id']
                )

            #next+token

            current_kwargs.update({
                'cursor_token': response_data['next_token'],
            })

            stopwatch.start()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=current_kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + '__next_token': {
                    'data': current_kwargs.copy(),
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertGreater(len(response_data['data']), 0)

            #[{event:event,originator:[],responder:[]}]
            for xx in range(settings.EVENT_QUANTITY_PER_PAGE, settings.EVENT_QUANTITY_PER_PAGE * 2):

                self.assertEqual(
                    all_expected_rows[x][xx].pk,
                    response_data['data'][xx - settings.EVENT_QUANTITY_PER_PAGE][all_kwargs[x]['audio_clip_role_name']][0]['id']
                )

            #back+token

            current_kwargs.update({
                'next_or_back': 'back',
                'cursor_token': response_data['back_token'],
            })

            stopwatch.start()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=current_kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + '__back_token': {
                    'data': current_kwargs.copy(),
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertGreater(len(response_data['data']), 0)

            #[{event:event,originator:[],responder:[]}]
            for xx in range(0, settings.EVENT_QUANTITY_PER_PAGE):

                self.assertEqual(
                    all_expected_rows[x][xx].pk,
                    response_data['data'][xx][all_kwargs[x]['audio_clip_role_name']][0]['id'])

            #back+token again, expect no rows

            current_kwargs.update({
                'next_or_back': 'back',
                'cursor_token': response_data['back_token'],
            })

            stopwatch.start()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=current_kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + '__back_token__no_rows': {
                    'data': current_kwargs.copy(),
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertEqual(len(response_data['data']), 0)

        #done

        self.metrics.update({inspect.currentframe().f_code.co_name: metrics})


    def test_browse_events__earliest_used_audio_clip_tone(self):

        logged_in_user = self.realistic_bulk_data_class.users[0]
        metrics = {}
        stopwatch = Stopwatch()

        self.login(logged_in_user)

        #==========
        #main page, only completed
        #==========

        latest_completed_kwargs = []
        latest_completed_expected_rows = []
        latest_completed_audio_clip_tone_ids = []

        #has tone
        for audio_clip_role_name in ['originator', 'responder']:
            target_row = AudioClips.objects.filter(
                audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                event__generic_status__generic_status_name='completed'
            ).order_by('-when_created', '-id').last()
            audio_clip_tone_id = target_row.audio_clip_tone.id
            latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
            latest_completed_kwargs.append({
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': audio_clip_role_name,
                'next_or_back': 'next',
                'audio_clip_tone_id': audio_clip_tone_id,
            })
            latest_completed_expected_rows.append(
                AudioClips.objects.filter(
                    audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    event__generic_status__generic_status_name='completed',
                    audio_clip_tone__id=audio_clip_tone_id,
                ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
            )

        #check test setup

        self.assertEqual(len(latest_completed_kwargs), len(latest_completed_audio_clip_tone_ids))
        self.assertEqual(len(latest_completed_kwargs), len(latest_completed_expected_rows))

        for expected_rows in latest_completed_expected_rows:

            self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

        #==========
        #user page, only completed
        #==========

        user_latest_completed_kwargs = []
        user_latest_completed_expected_rows = []
        user_latest_completed_audio_clip_tone_ids = []

        #has tone, username
        for audio_clip_role_name in ['originator', 'responder']:
            target_row = AudioClips.objects.filter(
                audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                event__generic_status__generic_status_name='completed',
                user__id=logged_in_user.id,
            ).order_by('-when_created', '-id').last()
            audio_clip_tone_id = target_row.audio_clip_tone.id
            user_latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
            user_latest_completed_kwargs.append({
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': audio_clip_role_name,
                'next_or_back': 'next',
                'audio_clip_tone_id': audio_clip_tone_id,
                'username': logged_in_user.username,
            })
            user_latest_completed_expected_rows.append(
                AudioClips.objects.filter(
                    audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    event__generic_status__generic_status_name='completed',
                    audio_clip_tone__id=audio_clip_tone_id,
                    user__id=logged_in_user.id,
                ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
            )

        #check test setup

        self.assertEqual(len(user_latest_completed_kwargs), len(user_latest_completed_audio_clip_tone_ids))
        self.assertEqual(len(user_latest_completed_kwargs), len(user_latest_completed_expected_rows))

        for expected_rows in user_latest_completed_expected_rows:

            self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

        #==========
        #own page, latest completed, likes dislikes
        #==========

        own_latest_completed_kwargs = []
        own_latest_completed_expected_rows = []
        own_latest_completed_audio_clip_tone_ids = []

        #has tone, username, likes/dislikes
        for audio_clip_role_name in ['originator', 'responder']:
            event_generic_status_names = []
            if audio_clip_role_name == 'originator':
                event_generic_status_names = ['incomplete', 'completed', 'deleted']
            else:
                event_generic_status_names = ['completed', 'deleted']
            for likes_or_dislikes_choice in ['likes', 'dislikes']:
                target_row = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                    user=logged_in_user,
                    audio_clip__event__generic_status__generic_status_name__in=event_generic_status_names,
                    audio_clip__generic_status__generic_status_name='ok',
                    audio_clip__audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    is_liked=(likes_or_dislikes_choice == 'likes'),
                ).order_by('-last_modified', '-id').last()
                audio_clip_tone_id = target_row.audio_clip.audio_clip_tone.id
                own_latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
                own_latest_completed_kwargs.append({
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': audio_clip_role_name,
                    'next_or_back': 'next',
                    'username': logged_in_user.username,
                    'likes_or_dislikes': likes_or_dislikes_choice,
                    'audio_clip_tone_id': audio_clip_tone_id,
                })
                like_dislike_rows = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                    user=logged_in_user,
                    audio_clip__event__generic_status__generic_status_name__in=event_generic_status_names,
                    audio_clip__generic_status__generic_status_name='ok',
                    audio_clip__audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    is_liked=(likes_or_dislikes_choice == 'likes'),
                    audio_clip__audio_clip_tone__id=audio_clip_tone_id,
                ).order_by('-last_modified', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2]
                expected_rows = []
                for row in like_dislike_rows:
                    expected_rows.append(row.audio_clip)
                own_latest_completed_expected_rows.append(expected_rows)

        #check test setup

        self.assertEqual(len(own_latest_completed_kwargs), len(own_latest_completed_audio_clip_tone_ids))
        self.assertEqual(len(own_latest_completed_kwargs), len(own_latest_completed_expected_rows))

        for expected_rows in own_latest_completed_expected_rows:

            self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

        #start

        all_kwargs = latest_completed_kwargs + user_latest_completed_kwargs + own_latest_completed_kwargs
        all_expected_rows = latest_completed_expected_rows + user_latest_completed_expected_rows + own_latest_completed_expected_rows

        for x in range(len(all_kwargs)):

            loop_title = f'loop#{str(x)}__'

            print(loop_title)

            #next

            stopwatch.start()

            current_kwargs:dict = all_kwargs[x].copy()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=current_kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + 'next__no_token': {
                    'data': current_kwargs.copy(),
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertGreater(len(response_data['data']), 0)

            #[{event:event,originator:[],responder:[]}]
            for xx in range(0, settings.EVENT_QUANTITY_PER_PAGE):

                self.assertEqual(
                    all_expected_rows[x][xx].pk,
                    response_data['data'][xx][all_kwargs[x]['audio_clip_role_name']][0]['id']
                )

            #next+token

            current_kwargs.update({
                'cursor_token': response_data['next_token'],
            })

            stopwatch.start()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=current_kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + 'next_token': {
                    'data': current_kwargs.copy(),
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertGreater(len(response_data['data']), 0)

            #[{event:event,originator:[],responder:[]}]
            for xx in range(settings.EVENT_QUANTITY_PER_PAGE, settings.EVENT_QUANTITY_PER_PAGE * 2):

                self.assertEqual(
                    all_expected_rows[x][xx].pk,
                    response_data['data'][xx - settings.EVENT_QUANTITY_PER_PAGE][all_kwargs[x]['audio_clip_role_name']][0]['id']
                )

            #back+token

            current_kwargs.update({
                'next_or_back': 'back',
                'cursor_token': response_data['back_token'],
            })

            stopwatch.start()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=current_kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + 'back_token': {
                    'data': current_kwargs.copy(),
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertGreater(len(response_data['data']), 0)

            #[{event:event,originator:[],responder:[]}]
            for xx in range(0, settings.EVENT_QUANTITY_PER_PAGE):

                self.assertEqual(
                    all_expected_rows[x][xx].pk,
                    response_data['data'][xx][all_kwargs[x]['audio_clip_role_name']][0]['id'])

            #back+token again, expect no rows

            current_kwargs.update({
                'next_or_back': 'back',
                'cursor_token': response_data['back_token'],
            })

            stopwatch.start()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=current_kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + 'back_token__no_rows': {
                    'data': current_kwargs.copy(),
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertEqual(len(response_data['data']), 0)

        #done

        self.metrics.update({inspect.currentframe().f_code.co_name: metrics})


    def test_browse_events__unused_audio_clip_tone(self):

        logged_in_user = self.realistic_bulk_data_class.users[0]
        metrics = {}
        stopwatch = Stopwatch()

        self.login(logged_in_user)

        for uact_loop_count, unused_audio_clip_tone_index in enumerate(self.realistic_bulk_data_class.excluded_audio_clip_tones_indexes):

            #==========
            #main page, only completed
            #==========

            latest_completed_kwargs = []
            latest_completed_expected_rows = []
            latest_completed_audio_clip_tone_ids = []

            #has tone
            for audio_clip_role_name in ['originator', 'responder']:
                audio_clip_tone_id = self.realistic_bulk_data_class.audio_clip_tones[unused_audio_clip_tone_index].id
                latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
                latest_completed_kwargs.append({
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': audio_clip_role_name,
                    'next_or_back': 'next',
                    'audio_clip_tone_id': audio_clip_tone_id,
                })
                latest_completed_expected_rows.append(
                    AudioClips.objects.filter(
                        audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        event__generic_status__generic_status_name='completed',
                        audio_clip_tone__id=audio_clip_tone_id,
                    ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
                )

            #check test setup

            self.assertEqual(len(latest_completed_kwargs), len(latest_completed_audio_clip_tone_ids))
            self.assertEqual(len(latest_completed_kwargs), len(latest_completed_expected_rows))

            for expected_rows in latest_completed_expected_rows:

                self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

            #==========
            #user page, only completed
            #==========

            user_latest_completed_kwargs = []
            user_latest_completed_expected_rows = []
            user_latest_completed_audio_clip_tone_ids = []

            #has tone, username
            for audio_clip_role_name in ['originator', 'responder']:
                audio_clip_tone_id = self.realistic_bulk_data_class.audio_clip_tones[unused_audio_clip_tone_index].id
                user_latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
                user_latest_completed_kwargs.append({
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': audio_clip_role_name,
                    'next_or_back': 'next',
                    'audio_clip_tone_id': audio_clip_tone_id,
                    'username': logged_in_user.username,
                })
                user_latest_completed_expected_rows.append(
                    AudioClips.objects.filter(
                        audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        event__generic_status__generic_status_name='completed',
                        audio_clip_tone__id=audio_clip_tone_id,
                        user__id=logged_in_user.id,
                    ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
                )

            #check test setup

            self.assertEqual(len(user_latest_completed_kwargs), len(user_latest_completed_audio_clip_tone_ids))
            self.assertEqual(len(user_latest_completed_kwargs), len(user_latest_completed_expected_rows))

            for expected_rows in user_latest_completed_expected_rows:

                self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

            #==========
            #own page, latest completed, likes dislikes
            #==========

            own_latest_completed_kwargs = []
            own_latest_completed_expected_rows = []
            own_latest_completed_audio_clip_tone_ids = []

            #has tone, originator, username, likes/dislikes
            for audio_clip_role_name in ['originator', 'responder']:
                event_generic_status_names = []
                if audio_clip_role_name == 'originator':
                    event_generic_status_names = ['incomplete', 'completed', 'deleted']
                else:
                    event_generic_status_names = ['completed', 'deleted']
                for likes_or_dislikes_choice in ['likes', 'dislikes']:
                    audio_clip_tone_id = self.realistic_bulk_data_class.audio_clip_tones[unused_audio_clip_tone_index].id
                    own_latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
                    own_latest_completed_kwargs.append({
                        'latest_or_best': 'latest',
                        'timeframe': 'all',
                        'audio_clip_role_name': audio_clip_role_name,
                        'next_or_back': 'next',
                        'username': logged_in_user.username,
                        'likes_or_dislikes': likes_or_dislikes_choice,
                        'audio_clip_tone_id': audio_clip_tone_id,
                    })
                    like_dislike_rows = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                        user=logged_in_user,
                        audio_clip__event__generic_status__generic_status_name__in=event_generic_status_names,
                        audio_clip__generic_status__generic_status_name='ok',
                        audio_clip__audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        is_liked=(likes_or_dislikes_choice == 'likes'),
                        audio_clip__audio_clip_tone__id=audio_clip_tone_id,
                    ).order_by('-last_modified', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2]
                    expected_rows = []
                    for row in like_dislike_rows:
                        expected_rows.append(row.audio_clip)
                    own_latest_completed_expected_rows.append(expected_rows)

            #check test setup

            self.assertEqual(len(own_latest_completed_kwargs), len(own_latest_completed_audio_clip_tone_ids))
            self.assertEqual(len(own_latest_completed_kwargs), len(own_latest_completed_expected_rows))

            for expected_rows in own_latest_completed_expected_rows:

                self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

            #start

            all_kwargs = latest_completed_kwargs + user_latest_completed_kwargs + own_latest_completed_kwargs
            all_expected_rows = latest_completed_expected_rows + user_latest_completed_expected_rows + own_latest_completed_expected_rows

            for x in range(len(all_kwargs)):

                loop_title = f'uact_loop_count#{str(uact_loop_count)}__loop#{x}__'

                print(loop_title)

                #next

                stopwatch.start()

                current_kwargs:dict = all_kwargs[x].copy()

                request = self.client.get(
                    reverse(
                        'browse_events_api',
                        kwargs=current_kwargs
                    )
                )

                stopwatch.end()

                metrics.update({
                    loop_title + 'next__no_token': {
                        'data': current_kwargs.copy(),
                        'time_s': stopwatch.diff_seconds(),
                    }
                })

                #check

                self.assertEqual(request.status_code, 200)

                #next_token, back_token, data
                response_data = get_response_data(request)

                self.assertGreater(len(response_data['data']), 0)

                #[{event:event,originator:[],responder:[]}]
                for xx in range(0, settings.EVENT_QUANTITY_PER_PAGE):

                    self.assertEqual(
                        all_expected_rows[x][xx].pk,
                        response_data['data'][xx][all_kwargs[x]['audio_clip_role_name']][0]['id']
                    )

                #next+token

                current_kwargs.update({
                    'cursor_token': response_data['next_token'],
                })

                stopwatch.start()

                request = self.client.get(
                    reverse(
                        'browse_events_api',
                        kwargs=current_kwargs
                    )
                )

                stopwatch.end()

                metrics.update({
                    loop_title + 'next_token': {
                        'data': current_kwargs.copy(),
                        'time_s': stopwatch.diff_seconds(),
                    }
                })

                #check

                self.assertEqual(request.status_code, 200)

                #next_token, back_token, data
                response_data = get_response_data(request)

                self.assertGreater(len(response_data['data']), 0)

                #[{event:event,originator:[],responder:[]}]
                for xx in range(settings.EVENT_QUANTITY_PER_PAGE, settings.EVENT_QUANTITY_PER_PAGE * 2):

                    self.assertEqual(
                        all_expected_rows[x][xx].pk,
                        response_data['data'][xx - settings.EVENT_QUANTITY_PER_PAGE][all_kwargs[x]['audio_clip_role_name']][0]['id']
                    )

                #back+token

                current_kwargs.update({
                    'next_or_back': 'back',
                    'cursor_token': response_data['back_token'],
                })

                stopwatch.start()

                request = self.client.get(
                    reverse(
                        'browse_events_api',
                        kwargs=current_kwargs
                    )
                )

                stopwatch.end()

                metrics.update({
                    loop_title + 'back_token': {
                        'data': current_kwargs.copy(),
                        'time_s': stopwatch.diff_seconds(),
                    }
                })

                #check

                self.assertEqual(request.status_code, 200)

                #next_token, back_token, data
                response_data = get_response_data(request)

                self.assertGreater(len(response_data['data']), 0)

                #[{event:event,originator:[],responder:[]}]
                for xx in range(0, settings.EVENT_QUANTITY_PER_PAGE):

                    self.assertEqual(
                        all_expected_rows[x][xx].pk,
                        response_data['data'][xx][all_kwargs[x]['audio_clip_role_name']][0]['id'])

                #back+token again, expect no rows

                current_kwargs.update({
                    'next_or_back': 'back',
                    'cursor_token': response_data['back_token'],
                })

                stopwatch.start()

                request = self.client.get(
                    reverse(
                        'browse_events_api',
                        kwargs=current_kwargs
                    )
                )

                stopwatch.end()

                metrics.update({
                    loop_title + 'back_token__no_rows': {
                        'data': current_kwargs.copy(),
                        'time_s': stopwatch.diff_seconds(),
                    }
                })

                #check

                self.assertEqual(request.status_code, 200)

                #next_token, back_token, data
                response_data = get_response_data(request)

                self.assertEqual(len(response_data['data']), 0)

        #done

        self.metrics.update({inspect.currentframe().f_code.co_name: metrics})


    def test_browse_events__all_apis__back_no_token__always_no_rows(self):

        #prepare all possible GET args here and test all at once, instead of separate context-related test cases

        #get any audio_clip_tone that is guaranteed to have rows

        audio_clip_tone = None

        excluded_audio_clip_tone_index = 0

        for row in self.realistic_bulk_data_class.audio_clip_tones:

            current_index = self.realistic_bulk_data_class.excluded_audio_clip_tones_indexes[excluded_audio_clip_tone_index]
            current_excluded_audio_clip_tone = self.realistic_bulk_data_class.audio_clip_tones[current_index]

            if row.id != current_excluded_audio_clip_tone.id:

                audio_clip_tone = row
                break

            excluded_audio_clip_tone_index += 1

        #start

        self.login(self.realistic_bulk_data_class.users[0])

        metrics = {}
        stopwatch = Stopwatch()

        #basic, back

        data_kwargs = [
            #no tone, completed
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'originator',
                'next_or_back': 'back',
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'responder',
                'next_or_back': 'back',
            },
            #has tone, completed
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'originator',
                'next_or_back': 'back',
                'audio_clip_tone_id': audio_clip_tone.id,
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'responder',
                'next_or_back': 'back',
                'audio_clip_tone_id': audio_clip_tone.id,
            },
            #no tone, completed, user
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'originator',
                'next_or_back': 'back',
                'username': self.realistic_bulk_data_class.users[0].username,
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'responder',
                'next_or_back': 'back',
                'username': self.realistic_bulk_data_class.users[0].username,
            },
            #has tone, completed, user
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'originator',
                'next_or_back': 'back',
                'audio_clip_tone_id': audio_clip_tone.id,
                'username': self.realistic_bulk_data_class.users[0].username,
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'responder',
                'next_or_back': 'back',
                'audio_clip_tone_id': audio_clip_tone.id,
                'username': self.realistic_bulk_data_class.users[0].username,
            },
            #no tone, user, likes/dislikes
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'originator',
                'next_or_back': 'back',
                'username': self.realistic_bulk_data_class.users[0].username,
                'likes_or_dislikes': 'likes',
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'originator',
                'next_or_back': 'back',
                'username': self.realistic_bulk_data_class.users[0].username,
                'likes_or_dislikes': 'dislikes',
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'responder',
                'next_or_back': 'back',
                'username': self.realistic_bulk_data_class.users[0].username,
                'likes_or_dislikes': 'likes',
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'responder',
                'next_or_back': 'back',
                'username': self.realistic_bulk_data_class.users[0].username,
                'likes_or_dislikes': 'dislikes',
            },
            #has tone, user, likes/dislikes
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'originator',
                'next_or_back': 'back',
                'username': self.realistic_bulk_data_class.users[0].username,
                'likes_or_dislikes': 'likes',
                'audio_clip_tone_id': audio_clip_tone.id,
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'originator',
                'next_or_back': 'back',
                'username': self.realistic_bulk_data_class.users[0].username,
                'likes_or_dislikes': 'dislikes',
                'audio_clip_tone_id': audio_clip_tone.id,
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'responder',
                'next_or_back': 'back',
                'username': self.realistic_bulk_data_class.users[0].username,
                'likes_or_dislikes': 'likes',
                'audio_clip_tone_id': audio_clip_tone.id,
            },
            {
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': 'responder',
                'next_or_back': 'back',
                'username': self.realistic_bulk_data_class.users[0].username,
                'likes_or_dislikes': 'dislikes',
                'audio_clip_tone_id': audio_clip_tone.id,
            },
        ]

        for index, data in enumerate(data_kwargs):

            stopwatch.start()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=data
                )
            )

            stopwatch.end()

            metrics.update({
                'loop_'+str(index): {
                    'data': data,
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertEqual(len(response_data['data']), 0)
            self.assertEqual(response_data['next_token'], '')
            self.assertEqual(response_data['back_token'], '')

        #done

        self.metrics.update({inspect.currentframe().f_code.co_name: metrics})


    def test_browse_events__all_apis__next_token__no_rows_left(self):

        logged_in_user = self.realistic_bulk_data_class.users[0]
        metrics = {}
        stopwatch = Stopwatch()

        self.login(logged_in_user)

        #==========
        #main page, only completed
        #==========

        latest_completed_kwargs = []
        latest_completed_expected_rows = []
        latest_completed_audio_clip_tone_ids = []

        #no tone
        for audio_clip_role_name in ['originator', 'responder']:
            target_row = AudioClips.objects.filter(
                audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                event__generic_status__generic_status_name='completed',
            ).order_by('-when_created', '-id').last()
            target_row_cursor_token = encode_cursor_token({
                'when_created': target_row.when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                'id': target_row.id,
            })
            audio_clip_tone_id = None
            latest_completed_audio_clip_tone_ids.append(None)
            latest_completed_kwargs.append({
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': audio_clip_role_name,
                'next_or_back': 'next',
                'cursor_token': target_row_cursor_token,
            })
            latest_completed_expected_rows.append(
                AudioClips.objects.filter(
                    audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    event__generic_status__generic_status_name='completed',
                ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
            )

        #has tone
        for audio_clip_role_name in ['originator', 'responder']:
            target_row = AudioClips.objects.filter(
                audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                event__generic_status__generic_status_name='completed',
            ).order_by('-when_created', '-id').last()
            target_row_cursor_token = encode_cursor_token({
                'when_created': target_row.when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                'id': target_row.id,
            })
            audio_clip_tone_id = target_row.audio_clip_tone.id
            latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
            latest_completed_kwargs.append({
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': audio_clip_role_name,
                'next_or_back': 'next',
                'cursor_token': target_row_cursor_token,
                'audio_clip_tone_id': audio_clip_tone_id,
            })
            latest_completed_expected_rows.append(
                AudioClips.objects.filter(
                    audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    audio_clip_tone__id=audio_clip_tone_id,
                    event__generic_status__generic_status_name='completed',
                ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
            )

        #check test setup

        self.assertEqual(len(latest_completed_kwargs), len(latest_completed_audio_clip_tone_ids))
        self.assertEqual(len(latest_completed_kwargs), len(latest_completed_expected_rows))

        for expected_rows in latest_completed_expected_rows:

            self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

        #==========
        #user page, only completed
        #==========

        user_latest_completed_kwargs = []
        user_latest_completed_expected_rows = []
        user_latest_completed_audio_clip_tone_ids = []

        #no tone, user
        for audio_clip_role_name in ['originator', 'responder']:
            target_row = AudioClips.objects.filter(
                audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                event__generic_status__generic_status_name='completed',
                user=logged_in_user,
            ).order_by('-when_created', '-id').last()
            target_row_cursor_token = encode_cursor_token({
                'when_created': target_row.when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                'id': target_row.id,
            })
            audio_clip_tone_id = None
            user_latest_completed_audio_clip_tone_ids.append(None)
            user_latest_completed_kwargs.append({
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': audio_clip_role_name,
                'next_or_back': 'next',
                'cursor_token': target_row_cursor_token,
                'username': logged_in_user.username,
            })
            user_latest_completed_expected_rows.append(
                AudioClips.objects.filter(
                    audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    event__generic_status__generic_status_name='completed',
                    user=logged_in_user,
                ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
            )

        #has tone, user
        for audio_clip_role_name in ['originator', 'responder']:
            target_row = AudioClips.objects.filter(
                audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                event__generic_status__generic_status_name='completed',
                user=logged_in_user,
            ).order_by('-when_created', '-id').last()
            target_row_cursor_token = encode_cursor_token({
                'when_created': target_row.when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                'id': target_row.id,
            })
            audio_clip_tone_id = target_row.audio_clip_tone.id
            user_latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
            user_latest_completed_kwargs.append({
                'latest_or_best': 'latest',
                'timeframe': 'all',
                'audio_clip_role_name': audio_clip_role_name,
                'next_or_back': 'next',
                'cursor_token': target_row_cursor_token,
                'audio_clip_tone_id': audio_clip_tone_id,
                'username': logged_in_user.username,
            })
            user_latest_completed_expected_rows.append(
                AudioClips.objects.filter(
                    audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    audio_clip_tone__id=audio_clip_tone_id,
                    event__generic_status__generic_status_name='completed',
                    user=logged_in_user,
                ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
            )

        #check test setup

        self.assertEqual(len(user_latest_completed_kwargs), len(user_latest_completed_audio_clip_tone_ids))
        self.assertEqual(len(user_latest_completed_kwargs), len(user_latest_completed_expected_rows))

        for expected_rows in user_latest_completed_expected_rows:

            self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

        #==========
        #own page, latest completed, likes dislikes
        #==========

        own_latest_completed_kwargs = []
        own_latest_completed_expected_rows = []
        own_latest_completed_audio_clip_tone_ids = []

        #no tone, user, like/dislike
        for audio_clip_role_name in ['originator', 'responder']:
            event_generic_status_names = []
            if audio_clip_role_name == 'originator':
                event_generic_status_names = ['incomplete', 'completed', 'deleted']
            else:
                event_generic_status_names = ['completed', 'deleted']
            for likes_or_dislikes_choice in ['likes', 'dislikes']:
                target_row = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                    user=logged_in_user,
                    audio_clip__event__generic_status__generic_status_name__in=event_generic_status_names,
                    audio_clip__generic_status__generic_status_name='ok',
                    audio_clip__audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    is_liked=(likes_or_dislikes_choice == 'likes'),
                ).order_by('-last_modified', '-id').last()
                target_row_cursor_token = encode_cursor_token({
                    'when_created': target_row.when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                    'id': target_row.id,
                })
                audio_clip_tone_id = None
                own_latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
                own_latest_completed_kwargs.append({
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': audio_clip_role_name,
                    'next_or_back': 'next',
                    'cursor_token': target_row_cursor_token,
                    'likes_or_dislikes': likes_or_dislikes_choice,
                    'username': logged_in_user.username,
                })
                like_dislike_rows = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                    user=logged_in_user,
                    audio_clip__event__generic_status__generic_status_name__in=event_generic_status_names,
                    audio_clip__generic_status__generic_status_name='ok',
                    audio_clip__audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    is_liked=(likes_or_dislikes_choice == 'likes'),
                ).order_by('-last_modified', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2]
                expected_rows = []
                for row in like_dislike_rows:
                    expected_rows.append(row.audio_clip)
                own_latest_completed_expected_rows.append(expected_rows)

        #has tone, user, like/dislike
        for audio_clip_role_name in ['originator', 'responder']:
            event_generic_status_names = []
            if audio_clip_role_name == 'originator':
                event_generic_status_names = ['incomplete', 'completed', 'deleted']
            else:
                event_generic_status_names = ['completed', 'deleted']
            for likes_or_dislikes_choice in ['likes', 'dislikes']:
                target_row = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                    user=logged_in_user,
                    audio_clip__event__generic_status__generic_status_name__in=event_generic_status_names,
                    audio_clip__generic_status__generic_status_name='ok',
                    audio_clip__audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    is_liked=(likes_or_dislikes_choice == 'likes'),
                ).order_by('-last_modified', '-id').last()
                target_row_cursor_token = encode_cursor_token({
                    'when_created': target_row.when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                    'id': target_row.id,
                })
                audio_clip_tone_id = target_row.audio_clip.audio_clip_tone.id
                own_latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
                own_latest_completed_kwargs.append({
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': audio_clip_role_name,
                    'next_or_back': 'next',
                    'cursor_token': target_row_cursor_token,
                    'likes_or_dislikes': likes_or_dislikes_choice,
                    'audio_clip_tone_id': audio_clip_tone_id,
                    'username': logged_in_user.username,
                })
                like_dislike_rows = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                    user=logged_in_user,
                    audio_clip__event__generic_status__generic_status_name__in=event_generic_status_names,
                    audio_clip__generic_status__generic_status_name='ok',
                    audio_clip__audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    audio_clip__audio_clip_tone__id=audio_clip_tone_id,
                    is_liked=(likes_or_dislikes_choice == 'likes'),
                ).order_by('-last_modified', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2]
                expected_rows = []
                for row in like_dislike_rows:
                    expected_rows.append(row.audio_clip)
                own_latest_completed_expected_rows.append(expected_rows)

        #check test setup

        self.assertEqual(len(own_latest_completed_kwargs), len(own_latest_completed_audio_clip_tone_ids))
        self.assertEqual(len(own_latest_completed_kwargs), len(own_latest_completed_expected_rows))

        for expected_rows in own_latest_completed_expected_rows:

            self.assertEqual(len(expected_rows), settings.EVENT_QUANTITY_PER_PAGE*2)

        #start

        all_kwargs = latest_completed_kwargs + user_latest_completed_kwargs + own_latest_completed_kwargs
        all_expected_rows = latest_completed_expected_rows + user_latest_completed_expected_rows + own_latest_completed_expected_rows

        for kwargs_count, kwargs in enumerate(all_kwargs):

            loop_title = f'loop{str(kwargs_count)}__'

            print(loop_title)

            #next+token, expect no rows

            stopwatch.start()

            request = self.client.get(
                reverse(
                    'browse_events_api',
                    kwargs=kwargs
                )
            )

            stopwatch.end()

            metrics.update({
                loop_title + 'next_token': {
                    'data': kwargs,
                    'time_s': stopwatch.diff_seconds(),
                }
            })

            #check

            self.assertEqual(request.status_code, 200)

            #next_token, back_token, data
            response_data = get_response_data(request)

            self.assertEqual(len(response_data['data']), 0)

            #next and back tokens should be the same
            self.assertEqual(response_data['next_token'], target_row_cursor_token)
            self.assertEqual(response_data['back_token'], target_row_cursor_token)

        #done

        self.metrics.update({inspect.currentframe().f_code.co_name: metrics})


    def test_list_event_reply_choices__ok(self):

        #current dilemma:
            #no real ordering, although can be unnecessary due to other conditions helping to narrow the range of rows
            #solutions
                #either try ORDER BY audio_clips.id ASC, or
                #do another "exclusive_events" WITH statement and join it
        pass


    def test_list_event_reply_choices__many_skipped(self):

        pass


    #do this first, finalise at API, then do the test cases above
    def test_new_list_event_reply_choices(self):

        #old
        #problem: provides no guaranteed ordering, making tests potentially unreliable, or have rows unexpectedly skipped
        def old(self, audio_clip_tone_id:int|None=None):

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
                    SELECT audio_clips.*,
                    audio_clip_likes_dislikes.is_liked AS is_liked_by_user
                    FROM audio_clips
                    INNER JOIN events ON audio_clips.event_id = events.id
                    LEFT JOIN event_reply_queues ON events.id = event_reply_queues.event_id
                    LEFT JOIN excluded_events_1 ON events.id = excluded_events_1.event_id
                    LEFT JOIN excluded_events_2 ON events.id = excluded_events_2.event_id
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


        #new0
        #ORDER BY audio_clips.when_created
        def new0(self, audio_clip_tone_id:int|None=None):

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
                    SELECT audio_clips.*,
                    audio_clip_likes_dislikes.is_liked AS is_liked_by_user
                    FROM audio_clips
                    INNER JOIN events ON audio_clips.event_id = events.id
                    LEFT JOIN event_reply_queues ON events.id = event_reply_queues.event_id
                    LEFT JOIN excluded_events_1 ON events.id = excluded_events_1.event_id
                    LEFT JOIN excluded_events_2 ON events.id = excluded_events_2.event_id
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
                    AND audio_clips.when_created >= %s
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
                    ORDER BY audio_clips.when_created ASC
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

















