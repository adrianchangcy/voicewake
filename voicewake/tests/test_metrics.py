from time import sleep
from django.test import TestCase, Client, TransactionTestCase, SimpleTestCase, override_settings
from django.test.runner import DiscoverRunner
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db import connection
from django.core.cache import cache
from django.db.models import Case, Value, When, Sum, Q, F, Count, BooleanField
from django.conf import settings
from django.db import connection, reset_queries
from django.contrib.auth.models import Group

from voicewake.models import *
from voicewake.services import *
from voicewake.factories import *

import math
from typing import Literal
import inspect
import time
import threading











#this is the only simple solution available
#***IMPORTANT***
#python manage.py test voicewake.tests.test_metrics.Your_TestCase --testrunner='voicewake.tests.test_metrics.TestRunnerWithMirror'
#***************
#custom test runner to allow for toggling of "MIRROR" at db
#since TEST_RUNNER cannot be changed via @override_settings, i.e. too late
class TestRunnerWithMirror(DiscoverRunner):

    def setup_databases(self, **kwargs):

        # Override DATABASES before test DB setup
        settings.DATABASES['default']['TEST'].update({'MIRROR': 'default'})
        return super().setup_databases(**kwargs)













#good balance of rows with same dates will test indexing better
#if you have too many rows to the point where it's unrealistic, space out data creation with time.sleep(1)
class RealisticBulkData():

    def __init__(
        self,
        db_batch_size=500,
    ):

        #SCENARIOS
            #for every scenario, must have None where no rows should exist
            #the None must always be placed as last item in array, so loops don't have to be painfully dynamic
            #order of scenarios in the combination must always be the same, e.g. don't block*processing then processing*block for new users

        #venn diagram
        #D[  A  ][C][  B  ]D
            #A blocks everyone
            #everyone blocks B
            #C blocks everyone and everyone blocks C
            #no blocking for D
        #needed for: UserBlocks
        #hence, ranges*scenarios at 3*4 means minimum 12 users
        self.user_block_scenarios = ['blocking', 'blocked', 'mutual_block', None]

        #processing_pending/processing/processing_failed or nothing
        self.processing_scenarios = [
            GenericStatuses.objects.get(generic_status_name='processing_pending'),
            GenericStatuses.objects.get(generic_status_name='processing'),
            GenericStatuses.objects.get(generic_status_name='processing_failed'),
            None
        ]

        self.db_batch_size = db_batch_size

        self.user_ids = get_user_model().objects.all().exclude(is_superuser=True).order_by('id').values_list('id', flat=True)

        #per-range quantity
        self.minimum_main_users_per_set = len(self.user_block_scenarios) * len(self.processing_scenarios)

        #there are some scenarios where you cannot reuse users, e.g. "1 responder per user"
        #"earliest" in old vs. new earliest/middle/latest will likely have some reused users
        #this helps prevent that
        self.is_newly_created_main_users = False

        self.main_user_group, is_created = Group.objects.get_or_create(name='RealisticBulkData_main_users')

        #we create our users in sets, and earliest/middle/latest is just picking sets across db
        #as long as the size of users in a set is constant,
        #self.get_main_users_relative_to_entire_db() will dynamically pick the sets as new rows are created
        self.main_user_sets = {
            'earliest': [],
            'middle': [],
            'latest': [],
        }

        #flattened from self.main_user_sets
        self.main_users = []

        #total quantity
        #self.main_user_sets is a flattened list of self.main_user_sets
        self.minimum_main_user_quantity = len(self.main_user_sets) * self.minimum_main_users_per_set
        self.main_user_prefix = "testuser"

        #this is for those users who will not be tested, e.g. users whose only purpose is to reply once
        self.filler_user_prefix = 'filleruser'

        #audio_file, use s3
        self.audio_file = settings.MEDIA_TEST_AWS_S3_START_PATH + '/audio_ok_10s.mp3'
        self.audio_volume_peaks = [0.2, 0.4, 0.8, 0.7, 0.5, 0.1, 0.2, 0.1, 0.4, 0.7, 0.3, 0.3, 0.5, 0.6, 0.4, 0.8, 0.7, 0.6, 0.2, 0.1]
        self.audio_duration_s = 26

        #2*minimum because our largest tests so far consist of "next" then "next+token" only
        self.event_quantity = 2 * settings.EVENT_QUANTITY_PER_PAGE

        self.generic_statuses = {
            'ok': GenericStatuses.objects.get(generic_status_name='ok'),
            'incomplete': GenericStatuses.objects.get(generic_status_name='incomplete'),
            'completed': GenericStatuses.objects.get(generic_status_name='completed'),
            'deleted': GenericStatuses.objects.get(generic_status_name='deleted'),
            'processing_pending': GenericStatuses.objects.get(generic_status_name='processing_pending'),
            'processing': GenericStatuses.objects.get(generic_status_name='processing'),
            'processing_failed': GenericStatuses.objects.get(generic_status_name='processing_failed'),
        }
        self.audio_clip_roles = {
            'originator': AudioClipRoles.objects.get(audio_clip_role_name='originator'),
            'responder': AudioClipRoles.objects.get(audio_clip_role_name='responder'),
        }

        #do same concept of earliest/middle/latest for tones for better index testing
        #we take full tones --> mark 2 "excluded" tones for each earliest/middle/latest --> add "normal" ones back into the full list
        #don't exclude "truly earliest"/"truly latest", e.g. [0], [-1]

        self.audio_clip_tones = []
        self.excluded_audio_clip_tones_indexes = []

        self._determine_audio_clip_tones()

        self.faulty_audio_file_unprocessed_object_key = 'test/text_as_fake_webm.webm'

        self.like_count = 0
        self.dislike_count = 0
        self.like_ratio = 0


    def _check_ready(self):

        if len(self.audio_clip_tones) == 0:

            raise ValueError('No tones fetched. Call .determine_audio_clip_tones() first.')

        if len(self.main_users) == 0:

            raise ValueError('No main users created. Call .create_new_users() first.')

        if self.like_count == 0 or self.dislike_count == 0 or self.like_ratio == 0:

            raise ValueError('Call .prepare_like_dislike_estimate() first.')


    @staticmethod
    def check_trigger(table_name:str, trigger_name:str, expect_enabled:bool):

        #::regclass
            #the cast to regclass gets you from qualified table name to OID the easy way
        #pg_get_triggerdef(pg_trigger.oid, pretty_print)
            #gives more details on trigger
            #for more internal postgresql functions:
                #https://www.postgresql.org/docs/current/functions-info.html
        #pg_trigger.tgenabled
            #controls in which session_replication_role modes the trigger fires
            #O = trigger fires in “origin” and “local” modes
            #D = trigger is disabled
            #R = trigger fires in “replica” mode
            #A = trigger fires always
        #NOT tgisinternal
            #filter out auto-generated triggers, e.g. re-created trigger with different tgname, or those for FKs
            #important to specify
                #if not, it will only return auto-gen triggers
                    #shown by pg_trigger.tgname having unrecognisable value

        rows = None

        with connection.cursor() as cursor:

            cursor.execute(
                '''
                    SELECT
                    trg.tgrelid, trg.tgname, pg_class.relname, trg.tgenabled, pg_get_triggerdef(trg.oid, true)
                    FROM pg_trigger AS trg
                    INNER JOIN pg_class ON trg.tgrelid = pg_class.oid
                    INNER JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
                    WHERE trg.tgrelid = %s::regclass
                    AND NOT tgisinternal;
                ''',
                [table_name]
            )

            rows = cursor.fetchmany()

        is_trigger_found = False
        test_case_class = TestCase()

        for row in rows:

            if row[1] == trigger_name:

                if expect_enabled is True:

                    test_case_class.assertEqual(row[3], 'O')

                else:

                    test_case_class.assertEqual(row[3], 'D')

                is_trigger_found = True
                break

        if is_trigger_found is False:

            raise ValueError('Trigger was not found.')


    #tones rarely change, so long-term implementation into it
    def _determine_audio_clip_tones(self):

        audio_clip_tones = AudioClipTones.objects.all().order_by('id')
        self.excluded_audio_clip_tones_indexes = []

        quantity_per_set = 5

        #check
        if len(audio_clip_tones) < (quantity_per_set * 3):

            raise ValueError(f'Total {len(audio_clip_tones)} tones is not enough, minimum {quantity_per_set*3} needed')

        new_full_audio_clip_tones = []
        excluded_audio_clip_tones = []

        #left 2 right 2 included, middle 1 excluded
        #math.floor() to find middle exclusion in a set will settle the 0-index adjustment
        quantity_per_set = 5

        #2+x+2, so value is 2
        quantity_per_included_side = int(math.floor(quantity_per_set - 1) / 2)

        #earliest

        excluded_index = quantity_per_included_side

        #earliest left
        for x in range(quantity_per_included_side):

            new_full_audio_clip_tones.append(audio_clip_tones[x])

        #earliest
        new_full_audio_clip_tones.append(audio_clip_tones[excluded_index])
        excluded_audio_clip_tones.append(audio_clip_tones[excluded_index])

        #earliest right
        for x in range((excluded_index + 1), quantity_per_set):

            new_full_audio_clip_tones.append(audio_clip_tones[x])

        #middle

        excluded_index = math.floor(len(audio_clip_tones) / 2)

        #middle left
        for x in range((excluded_index - quantity_per_included_side), excluded_index):

            new_full_audio_clip_tones.append(audio_clip_tones[x])

        #middle
        new_full_audio_clip_tones.append(audio_clip_tones[excluded_index])
        excluded_audio_clip_tones.append(audio_clip_tones[excluded_index])

        #middle right
        for x in range((excluded_index + 1), (excluded_index + 1 + quantity_per_included_side)):

            new_full_audio_clip_tones.append(audio_clip_tones[x])

        #latest

        excluded_index = len(audio_clip_tones) - 1 - quantity_per_included_side

        #latest left
        for x in range((excluded_index - quantity_per_included_side), excluded_index):

            new_full_audio_clip_tones.append(audio_clip_tones[x])

        #latest
        new_full_audio_clip_tones.append(audio_clip_tones[excluded_index])
        excluded_audio_clip_tones.append(audio_clip_tones[excluded_index])

        #latest right
        for x in range((excluded_index + 1), len(audio_clip_tones)):

            new_full_audio_clip_tones.append(audio_clip_tones[x])

        #from new full tones, get excluded indexes of that array

        self.audio_clip_tones = new_full_audio_clip_tones

        excluded_index_checkpoint = 0

        for index, audio_clip_tone in enumerate(self.audio_clip_tones):

            if audio_clip_tone.id == excluded_audio_clip_tones[excluded_index_checkpoint].id:

                self.excluded_audio_clip_tones_indexes.append(index)
                excluded_index_checkpoint += 1

                if excluded_index_checkpoint == 3:

                    break

        #check

        #check quantity
        if (
            len(self.audio_clip_tones) == (quantity_per_set * 3) and
            len(self.excluded_audio_clip_tones_indexes) == 3
        ) is False:

            raise ValueError(f'Invalid: {len(self.audio_clip_tones)} total tones, {len(self.excluded_audio_clip_tones_indexes)} excluded')

        #check order
        for x in range(len(self.audio_clip_tones)):

            try:

                target_audio_clip_tone = self.audio_clip_tones[x+1]

            except:

                #is at last element
                break

            #current must always be smaller than next
            if self.audio_clip_tones[x].id >= target_audio_clip_tone.id:

                raise ValueError(f'Tone id out of order: {self.audio_clip_tones[x].id} and {target_audio_clip_tone.id}')

        #check position of excluded indexes
        #reminder that quantity_per_included_side is for included rows except the excluded row, e.g. 2+x+2, so value is 2
        if self.excluded_audio_clip_tones_indexes[0] != quantity_per_included_side:

            raise ValueError(f'Excluded array index mismatch: {self.excluded_audio_clip_tones_indexes[0]}')

        if self.excluded_audio_clip_tones_indexes[1] != quantity_per_set + quantity_per_included_side:

            raise ValueError(f'Excluded array index mismatch: {self.excluded_audio_clip_tones_indexes[1]}')

        if self.excluded_audio_clip_tones_indexes[2] != (quantity_per_set * 2) + quantity_per_included_side:

            raise ValueError(f'Excluded array index mismatch: {self.excluded_audio_clip_tones_indexes[2]}')


    #main users in db are in sets
    #earliest/middle/latest is just about selecting from these sets, e.g. earliest = earliest set in db
    #for newly created main users, they will fully occupy earliest/middle/latest here, and does not actually retrieve "true earliest/etc." from db
    def create_new_users(self, user_quantity=None, user_type:Literal['main', 'filler']='main'):

        target_user_quantity = self.minimum_main_user_quantity

        if user_quantity is not None:

            target_user_quantity = user_quantity

        #get last user in db

        user_count = 0
        target_user_prefix = self.main_user_prefix

        if user_type == 'filler':

            target_user_prefix = self.filler_user_prefix

        latest_test_user = get_user_model().objects.filter(username_lowercase__startswith=target_user_prefix).order_by('-id')[:1]

        if len(latest_test_user) == 1:

            latest_test_user = latest_test_user[0]

            print('Found latest user by username_lowercase: ' + latest_test_user.username_lowercase)

            #separate "99" from "test_user99@gmail.com"
            latest_test_user_index = latest_test_user.username_lowercase.split(target_user_prefix)
            latest_test_user_index = int(latest_test_user_index[1])

            #if latest user is username99, we set starting count to 100 when creating new users
            user_count = latest_test_user_index + 1

        #create users and add to group

        if user_type == 'main':

            #reset
            self.main_users = []

            #create by per-set basis
            for set_name in self.main_user_sets:

                new_users = []

                for x in range(user_count, user_count+self.minimum_main_users_per_set):

                    new_username = self.main_user_prefix + str(x)
                    new_email = new_username + '@gmail.com'

                    new_users.append(
                        get_user_model().objects.create_user(
                            username=new_username,
                            email=new_email,
                            is_active=True,
                        )
                    )

                    self.main_user_group.user_set.add(new_users[-1])

                    print('Created test user: ' + new_users[-1].username)

                self.main_user_sets[set_name] = new_users
                self.main_users.extend(new_users)

                user_count += self.minimum_main_users_per_set

            self.is_newly_created_main_users = True

            return self.main_users

        elif user_type == 'filler':

            new_users = []

            #no need to track filler users using groups so far

            for x in range(user_count, user_count+target_user_quantity):

                new_username = self.filler_user_prefix + str(x)
                new_email = new_username + '@gmail.com'

                new_users.append(
                    get_user_model().objects.create_user(
                        username=new_username,
                        email=new_email,
                        is_active=True,
                    )
                )

                print('Created test user: ' + new_users[-1].username)

            return new_users

        else:

            raise ValueError(f'invalid {user_type}')


    #earliest/middle/latest users implies entire db
    #as users increase, we must still reliably retrieve across earliest/middle/latest sets in db
    #WARNING: do not use this to create new rows, else earliest set is infinitely reused
    #enforce this by doing @staticmethod
    @staticmethod
    def get_main_users_relative_to_entire_db():

        realistic_bulk_data_class = RealisticBulkData()

        main_users = []
        main_user_sets = realistic_bulk_data_class.main_user_sets.copy()

        #get count of users -> check if scenario combinations still match user count

        total_main_user_count = realistic_bulk_data_class.main_user_group.user_set.all().count()

        if total_main_user_count == 0:

            raise ValueError('no users found')

        if (total_main_user_count % realistic_bulk_data_class.minimum_main_user_quantity) != 0:

            raise ValueError('combination of scenarios and main_users did not match. please recreate db.')

        #get earliest and latest because it's easy

        #0 to x
        earliest_main_users = realistic_bulk_data_class.main_user_group.user_set.all().order_by('id')[
            0 : realistic_bulk_data_class.minimum_main_users_per_set
        ]

        #total-x (from-0 index) to total
        #for [offset:limit], Django requires [offset:limit+offset]
        latest_main_users = realistic_bulk_data_class.main_user_group.user_set.all().order_by('id')[
            total_main_user_count - realistic_bulk_data_class.minimum_main_users_per_set : total_main_user_count
        ]

        #handle middle

        #find out how many sets first
        #can't just directly half, else it won't guarantee set order
        middle_main_user_index = total_main_user_count / realistic_bulk_data_class.minimum_main_users_per_set

        #get most middle set
        middle_main_user_index = math.floor(middle_main_user_index / 2)

        #get starting index of middle set
        middle_main_user_index = (middle_main_user_index * realistic_bulk_data_class.minimum_main_users_per_set)

        #for [offset:limit], Django requires [offset:limit+offset]
        middle_main_users = realistic_bulk_data_class.main_user_group.user_set.all().order_by('id')[
            middle_main_user_index : realistic_bulk_data_class.minimum_main_users_per_set + middle_main_user_index
        ]

        #add to realistic_bulk_data_class.main_users and realistic_bulk_data_class.main_user_sets
        main_users.extend(earliest_main_users)
        main_users.extend(middle_main_users)
        main_users.extend(latest_main_users)

        main_user_sets['earliest'] = earliest_main_users
        main_user_sets['middle'] = middle_main_users
        main_user_sets['latest'] = latest_main_users

        return {
            'main_users': main_users,
            'main_user_sets': main_user_sets,
        }


    def prepare_like_dislike_estimate(self):

        if self.minimum_main_user_quantity < 10:

            raise ValueError('To keep things simple, please maintain a minimum of 10.')

        if len(self.main_users) == 0:

            raise ValueError('No users. Call .create_new_users() first.')

        #to prevent full exponential scaling, allow an amount of users to not vote at every audio_clip

        #len(users) must not be divisible by (like_count + dislike_count), else one user has only likes, the other dislikes, etc.
        #this is easily achieved by doing (len(users)/2)+1
        #better +1 than -1, since having too few also means some users have only likes/dislikes
        self.like_count = math.ceil(len(self.main_users) * 0.25)
        self.dislike_count = math.ceil(len(self.main_users) * 0.5) + 1

        self.like_ratio = (self.like_count / (self.like_count + self.dislike_count))


    #initially though only running this once for all create() is more efficient
    #but that doesn't help when everything is too slow, so this will be coupled into all individual create(), then use threading to execute
    def _create_audio_clip_likes_dislikes(self, audio_clips):

        full_sql = ''
        full_params = []

        #likes dislikes
        #len(users) must not be divisible by (like_count + dislike_count), else one user has only likes, the other dislikes, etc.

        datetime_now = get_datetime_now()

        full_sql += 'INSERT INTO audio_clip_likes_dislikes (user_id, audio_clip_id, is_liked, when_created, last_modified) VALUES '

        user_index = 0

        for audio_clip in audio_clips:

            current_like_count = 0
            current_dislike_count = 0
            current_user = None

            #likes
            while current_like_count < self.like_count:

                try:

                    current_user = self.main_users[user_index]

                except IndexError:

                    user_index = 0
                    current_user = self.main_users[user_index]

                full_sql += '(%s,%s,%s,%s,%s),'
                full_params.extend([
                    current_user.id,
                    audio_clip.id,
                    True,
                    datetime_now,
                    datetime_now,
                ])

                user_index += 1
                current_like_count += 1

            #dislikes
            while current_dislike_count < self.dislike_count:

                try:

                    current_user = self.main_users[user_index]

                except IndexError:

                    user_index = 0
                    current_user = self.main_users[user_index]

                full_sql += '(%s,%s,%s,%s,%s),'
                full_params.extend([
                    current_user.id,
                    audio_clip.id,
                    False,
                    datetime_now,
                    datetime_now,
                ])

                user_index += 1
                current_dislike_count += 1

        #remove the final ',' from final audio_clip row
        full_sql = full_sql[:len(full_sql)-1]
        full_sql += ' '

        #get PK only
        full_sql += 'RETURNING audio_clip_likes_dislikes.id;'

        with connection.cursor() as cursor:

            cursor.execute(full_sql, full_params)


    def _tbd_combination_index_finder(
        self,
        block_scenario:Literal['block', 'blocked', 'mutual_block', None]=None,
        processing_scenario:Literal['processing_pending', 'processing', 'processing_failed', None]=None,
    ):

        #consistent order matters, e.g. block*processing and processing*block will have different final ordering
        scenario_0 = ['block', 'blocked', 'mutual_block', None]
        scenario_1 = ['processing_pending', 'processing', 'processing_failed', None]

        def lazy_inefficient():

            #combine first
            combined_scenarios = []

            for x in scenario_0:
                for y in scenario_1:
                    combined_scenarios.append([x,y])

            for index, combined_scenario in enumerate(combined_scenarios):

                if combined_scenario[0] == block_scenario and combined_scenario[1] == processing_scenario:

                    return index

        def more_like_breadth_first_search():

            index = 0

            for x in scenario_0:

                #multiply downwards until the end when it doesn't match up here
                #e.g. if skipping scenario_0 when there's scenario_1 and scenario_2, do len(scenario_1) * len(scenario_2)
                if x != scenario_0:

                    #no -1 because we're starting next loop immediately
                    #if next is coincidentally true, returns accurately
                    index += len(scenario_1)
                    continue

                for y in scenario_1:

                    if y != scenario_1:

                        #only +1 for last combination because it's x*(y...y)
                        index += 1
                        continue

                    return index


    def create_event_incomplete(self, skipped_by_users:bool=False):

        self._check_ready()

        events = []
        originator_audio_clips = []
        originator_audio_clip_metrics = []
        user_events = []
        when_excluded_for_reply = get_datetime_now() - timedelta(seconds=20)

        print_with_function_name(f"Started. skipped_by_users={str(skipped_by_users)}.")

        stopwatch = Stopwatch()

        for audio_clip_tone_index, audio_clip_tone in enumerate(self.audio_clip_tones):

            #skip audio_clip_tone
            if audio_clip_tone_index in self.excluded_audio_clip_tones_indexes:

                print('Skipping excluded audio_clip_tones.')
                continue

            stopwatch.start()

            #events
            temp_events = []

            for user in self.main_users:

                #events must exist in db first before audio_clips, so we create them here
                temp_events.extend(
                    EventsFactory.create_batch(
                        event_created_by=user,
                        event_generic_status_generic_status_name='incomplete',
                        size=self.event_quantity,
                    )
                )
                reset_queries()

            events.extend(temp_events)

            #audio_clips, event_reply_queues, user_events

            for event in temp_events:

                originator_audio_clips.append(
                    AudioClips(
                        user=event.created_by,
                        audio_clip_role=self.audio_clip_roles['originator'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=self.generic_statuses['ok'],
                        audio_file=self.audio_file,
                        audio_duration_s=self.audio_duration_s,
                        audio_volume_peaks=self.audio_volume_peaks,
                        is_banned=False,
                    )
                )

                #users who have skipped before
                #we refer to existing user in event_reply_queues if is_replying=True, so we don't have the same user skipping and replying

                if skipped_by_users is True:

                    for user in self.main_users:

                        if event.created_by_id == user.id:

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

            stopwatch.stop()
            print(f'Done with audio_clip_tone #{audio_clip_tone_index}.')
            stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clips...')

        originator_audio_clips = AudioClips.objects.bulk_create(originator_audio_clips, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clip_metrics...')

        for audio_clip in originator_audio_clips:

            originator_audio_clip_metrics.append(
                AudioClipMetrics(
                    None,
                    audio_clip=audio_clip,
                    like_count=0,
                    dislike_count=0,
                    like_ratio=0,
                )
            )

        originator_audio_clip_metrics = AudioClipMetrics.objects.bulk_create(originator_audio_clip_metrics, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating user_events...')

        if skipped_by_users is True:

            user_events = UserEvents.objects.bulk_create(user_events, batch_size=self.db_batch_size)
            reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clip_likes_dislikes...')

        self._create_audio_clip_likes_dislikes(originator_audio_clips)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        return {
            'events': events,
            'originator_audio_clips': originator_audio_clips,
            'originator_audio_clip_metrics': originator_audio_clip_metrics,
            'user_events': user_events,
            'when_excluded_for_reply': when_excluded_for_reply,
        }


    #call only once per new set of users
    def create_event_incomplete_and_event_reply_queue(self, is_replying:bool=False):

        #since 1 user can only have 1 queue for 1 event, we create queues separately from new events

        self._check_ready()

        print_with_function_name(f'Started. is_replying={is_replying},')

        events = []
        event_reply_queues = []
        originator_audio_clips = []
        originator_audio_clip_metrics = []
        when_locked = get_datetime_now() - timedelta(seconds=10)

        stopwatch = Stopwatch()

        #easiest way to prevent non-indentical users between originator and responder is to create new events

        audio_clip_tone = self.audio_clip_tones[0]

        stopwatch.start()
        print('Creating events...')

        for user in self.main_users:

            events.append(
                Events(
                    event_name='hoo',
                    created_by=user,
                    generic_status=self.generic_statuses['incomplete'],
                )
            )

        events = Events.objects.bulk_create(events, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clips...')

        for event in events:

            originator_audio_clips.append(
                AudioClips(
                    user=event.created_by,
                    audio_clip_role=self.audio_clip_roles['originator'],
                    audio_clip_tone=audio_clip_tone,
                    event=event,
                    generic_status=self.generic_statuses['ok'],
                    audio_file=self.audio_file,
                    audio_duration_s=self.audio_duration_s,
                    audio_volume_peaks=self.audio_volume_peaks,
                    is_banned=False,
                )
            )

        originator_audio_clips = AudioClips.objects.bulk_create(originator_audio_clips, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clip_metrics...')

        for audio_clip in originator_audio_clips:

            originator_audio_clip_metrics.append(
                AudioClipMetrics(
                    audio_clip=audio_clip,
                    like_count=0,
                    dislike_count=0,
                    like_ratio=0,
                )
            )

        originator_audio_clip_metrics = AudioClipMetrics.objects.bulk_create(originator_audio_clip_metrics, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating event_reply_queues...')

        #add last queue first, so no if-check is needed at every iteration
        event_reply_queues.append(
            EventReplyQueues(
                event=events[-1],
                locked_for_user=self.main_users[-1],
                is_replying=is_replying,
            )
        )

        index = 0

        #will reliably exit when locked_for_user raises IndexError
        #since we already created that object above
        try:

            while index < len(events):

                event_reply_queues.append(
                    EventReplyQueues(
                        event=events[index],
                        locked_for_user=self.main_users[index+1],
                        is_replying=is_replying,
                    )
                )

                index += 1

        except IndexError:

            pass

        event_reply_queues = EventReplyQueues.objects.bulk_create(event_reply_queues, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        return {
            'events': events,
            'event_reply_queues': event_reply_queues,
            'originator_audio_clips': originator_audio_clips,
            'originator_audio_clip_metrics': originator_audio_clip_metrics,
            'when_locked': when_locked,
        }


    def create_event_completed(self):

        self._check_ready()

        events = []
        originator_audio_clips = []
        responder_audio_clips = []
        originator_audio_clip_metrics = []
        responder_audio_clip_metrics = []

        print_with_function_name(f"Started.")

        datetime_now = get_datetime_now()
        stopwatch = Stopwatch()

        for audio_clip_tone_index, audio_clip_tone in enumerate(self.audio_clip_tones):

            #skip audio_clip_tone
            if audio_clip_tone_index in self.excluded_audio_clip_tones_indexes:

                print('Skipping excluded audio_clip_tones.')
                continue

            stopwatch.start()

            #events
            temp_events = []

            for user in self.main_users:

                #if we only need originator, use current user
                #if we need responder, use user_index+1

                #create events, audio_clips, audio_clip_likes_dislikes
                #create extra "incomplete" events that are in the midst of replying

                #events must exist before audio_clips
                temp_events.extend(
                    EventsFactory.create_batch(
                        event_created_by=user,
                        event_generic_status_generic_status_name='completed',
                        size=self.event_quantity,
                    )
                )
                reset_queries()

            events.extend(temp_events)

            #audio_clips

            responder_user_index = 0

            for event in temp_events:

                originator_audio_clips.append(
                    AudioClips(
                        user=event.created_by,
                        audio_clip_role=self.audio_clip_roles['originator'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=self.generic_statuses['ok'],
                        audio_file=self.audio_file,
                        audio_duration_s=self.audio_duration_s,
                        audio_volume_peaks=self.audio_volume_peaks,
                        is_banned=False,
                    )
                )

                #for responder, we +1 self.main_user_sets until the end, then restart from 0
                #originator and responder cannot be the same
                responder = None

                try:

                    #use this statement to check for IndexError
                    #also might as well +=1 if users are the same
                    if self.main_users[responder_user_index] == event.created_by.id:

                        responder_user_index += 1

                except IndexError:

                    #out of range, restart
                    responder_user_index = 0

                    if self.main_users[responder_user_index] == event.created_by.id:

                        responder_user_index += 1

                responder = self.main_users[responder_user_index]
                responder_user_index += 1

                responder_audio_clips.append(
                    AudioClips(
                        user=responder,
                        audio_clip_role=self.audio_clip_roles['responder'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=self.generic_statuses['ok'],
                        audio_file=self.audio_file,
                        audio_duration_s=self.audio_duration_s,
                        audio_volume_peaks=self.audio_volume_peaks,
                        is_banned=False,
                    )
                )

            stopwatch.stop()
            print(f'Done with audio_clip_tone #{audio_clip_tone_index}.')
            stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clips...')

        originator_audio_clips = AudioClips.objects.bulk_create(originator_audio_clips, batch_size=self.db_batch_size)
        responder_audio_clips = AudioClips.objects.bulk_create(responder_audio_clips, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clip_metrics...')

        for audio_clip in originator_audio_clips:

            originator_audio_clip_metrics.append(
                AudioClipMetrics(
                    None,
                    audio_clip.id,
                    0,
                    0,
                    0,
                    datetime_now,
                    datetime_now
                )
            )

        for audio_clip in responder_audio_clips:

            responder_audio_clip_metrics.append(
                AudioClipMetrics(
                    None,
                    audio_clip.id,
                    0,
                    0,
                    0,
                    datetime_now,
                    datetime_now
                )
            )

        originator_audio_clip_metrics = AudioClipMetrics.objects.bulk_create(originator_audio_clip_metrics, batch_size=self.db_batch_size)
        responder_audio_clip_metrics = AudioClipMetrics.objects.bulk_create(responder_audio_clip_metrics, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clip_likes_dislikes...')

        self._create_audio_clip_likes_dislikes(originator_audio_clips)
        self._create_audio_clip_likes_dislikes(responder_audio_clips)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        return {
            'events': events,
            'originator_audio_clips': originator_audio_clips,
            'responder_audio_clips': responder_audio_clips,
            'originator_audio_clip_metrics': originator_audio_clip_metrics,
            'responder_audio_clip_metrics': responder_audio_clip_metrics,
        }


    def create_event_deleted(self, has_responder:bool, is_originator_banned:bool, is_responder_banned:bool=False):

        if (
            #can't specify responder to be banned if no responder
            (has_responder is False and is_responder_banned is True) or
            #don't create incomplete events using this function
            (has_responder is False and is_originator_banned is False)
        ):

            raise ValueError('Invalid arg combination.')

        self._check_ready()

        events = []
        originator_audio_clips = []
        responder_audio_clips = []
        originator_audio_clip_metrics = []
        responder_audio_clip_metrics = []

        print_with_function_name(
            f'''
            Started.
            has_responder={str(has_responder)},
            is_originator_banned={str(is_originator_banned)},
            is_responder_banned={str(is_responder_banned)},
            '''
        )

        #decide event and audio_clip statuses in advance

        event_generic_status = None
        originator_audio_clip_generic_status = None
        responder_audio_clip_generic_status = None

        if has_responder is True:

            if is_originator_banned is True and is_responder_banned is True:

                event_generic_status = self.generic_statuses['deleted']
                originator_audio_clip_generic_status = self.generic_statuses['deleted']
                responder_audio_clip_generic_status = self.generic_statuses['deleted']

            elif is_originator_banned is True and is_responder_banned is False:

                event_generic_status = self.generic_statuses['deleted']
                originator_audio_clip_generic_status = self.generic_statuses['deleted']
                responder_audio_clip_generic_status = self.generic_statuses['ok']

            elif is_originator_banned is False and is_responder_banned is True:

                event_generic_status = self.generic_statuses['incomplete']
                originator_audio_clip_generic_status = self.generic_statuses['ok']
                responder_audio_clip_generic_status = self.generic_statuses['deleted']

        else:

                event_generic_status = self.generic_statuses['deleted']
                originator_audio_clip_generic_status = self.generic_statuses['deleted']

        stopwatch = Stopwatch()

        for audio_clip_tone_index, audio_clip_tone in enumerate(self.audio_clip_tones):

            #skip audio_clip_tone
            if audio_clip_tone_index in self.excluded_audio_clip_tones_indexes:

                print('Skipping excluded audio_clip_tones.')
                continue

            stopwatch.start()

            #events
            temp_events = []

            for user in self.main_users:

                #if we only need originator, use current user
                #if we need responder, use user_index+1

                #create events, audio_clips, audio_clip_likes_dislikes
                #create extra "incomplete" events that are in the midst of replying

                #events must exist before audio_clips
                temp_events.extend(
                    EventsFactory.create_batch(
                        event_created_by=user,
                        event_generic_status_generic_status_name=event_generic_status.generic_status_name,
                        size=self.event_quantity,
                    )
                )
                reset_queries()

            events.extend(temp_events)

            #audio_clips

            responder_user_index = 0

            for event in temp_events:

                originator_audio_clips.append(
                    AudioClips(
                        user=event.created_by,
                        audio_clip_role=self.audio_clip_roles['originator'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=originator_audio_clip_generic_status,
                        audio_file=self.audio_file,
                        audio_duration_s=self.audio_duration_s,
                        audio_volume_peaks=self.audio_volume_peaks,
                        is_banned=is_originator_banned,
                    )
                )

                if has_responder is False:

                    continue

                #for responder, we +1 self.main_users until the end, then restart from 0
                #originator and responder cannot be the same
                responder = None

                try:

                    #use this statement to check for IndexError
                    #also might as well +=1 if users are the same
                    if self.main_users[responder_user_index] == event.created_by.id:

                        responder_user_index += 1

                except IndexError:

                    #out of range, restart
                    responder_user_index = 0

                    if self.main_users[responder_user_index] == event.created_by.id:

                        responder_user_index += 1

                responder = self.main_users[responder_user_index]
                responder_user_index += 1

                responder_audio_clips.append(
                    AudioClips(
                        user=responder,
                        audio_clip_role=self.audio_clip_roles['responder'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=responder_audio_clip_generic_status,
                        audio_file=self.audio_file,
                        audio_duration_s=self.audio_duration_s,
                        audio_volume_peaks=self.audio_volume_peaks,
                        is_banned=is_responder_banned,
                    )
                )

            stopwatch.stop()
            print(f'Done with audio_clip_tone #{audio_clip_tone_index}.')
            stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clips...')

        originator_audio_clips = AudioClips.objects.bulk_create(originator_audio_clips, batch_size=self.db_batch_size)
        responder_audio_clips = AudioClips.objects.bulk_create(responder_audio_clips, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clip_metrics...')

        for audio_clip in originator_audio_clips:

            originator_audio_clip_metrics.append(
                AudioClipMetrics(
                    audio_clip=audio_clip,
                    like_count=0,
                    dislike_count=0,
                    like_ratio=0,
                )
            )

        for audio_clip in responder_audio_clips:

            responder_audio_clip_metrics.append(
                AudioClipMetrics(
                    audio_clip=audio_clip,
                    like_count=0,
                    dislike_count=0,
                    like_ratio=0,
                )
            )

        originator_audio_clip_metrics = AudioClipMetrics.objects.bulk_create(originator_audio_clip_metrics, batch_size=self.db_batch_size)
        responder_audio_clip_metrics = AudioClipMetrics.objects.bulk_create(responder_audio_clip_metrics, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clip_likes_dislikes...')

        self._create_audio_clip_likes_dislikes(originator_audio_clips)

        if len(responder_audio_clips) > 0:

            self._create_audio_clip_likes_dislikes(responder_audio_clips)

        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        return {
            'events': events,
            'originator_audio_clips': originator_audio_clips,
            'responder_audio_clips': responder_audio_clips,
            'originator_audio_clip_metrics': originator_audio_clip_metrics,
            'responder_audio_clip_metrics': responder_audio_clip_metrics,
        }


    #originator can have infinite combination of processing/processing_pending/processing_failed audio_clips
    #hence, minimum_user_quantity is used purely to maintain structure of "sets" in db
    def create_processing_originators(self, user_type:Literal['main', 'filler'], events_per_user_per_processing_scenario=1):

        #1 originator can have a few processing_pending/processing/processing_failed
        originators = []
        
        if user_type == 'main':

            originators = self.main_users

        else:

            originators = self.create_new_users(
                user_quantity=self.minimum_main_user_quantity,
                user_type='filler'
            )

        events = []
        originator_audio_clips = []
        originator_audio_clip_metrics = []

        stopwatch = Stopwatch()

        print_with_function_name(f"Started.")
        stopwatch.start()

        #since each originator can have multiple rows, no need to care about the scenario*scenario part

        #we do user*processing_scenarios so it's as consistent to test as for create_processing_responders()
        for user in originators:

            for target_generic_status in self.processing_scenarios:

                if target_generic_status is None:

                    continue

                #events must exist in db first before audio_clips, so we create them here
                events.extend(
                    EventsFactory.create_batch(
                        event_created_by=user,
                        event_generic_status_generic_status_name='processing',
                        size=events_per_user_per_processing_scenario
                    )
                )
                reset_queries()

                temporary_event_index = len(events) - events_per_user_per_processing_scenario

                for x in range(events_per_user_per_processing_scenario):

                    #randomise tone just because it's easier to code
                    audio_clip_tone_index = random.randint(0, (len(self.audio_clip_tones) - 1))

                    #for benchmarks, excluded tones must be left alone
                    while audio_clip_tone_index in self.excluded_audio_clip_tones_indexes:

                        #reroll
                        audio_clip_tone_index = random.randint(0, (len(self.audio_clip_tones) - 1))

                    audio_clip_tone = self.audio_clip_tones[audio_clip_tone_index]

                    originator_audio_clips.append(
                        AudioClips(
                            user=events[temporary_event_index+x].created_by,
                            audio_clip_role=self.audio_clip_roles['originator'],
                            audio_clip_tone=audio_clip_tone,
                            event=events[temporary_event_index+x],
                            generic_status=target_generic_status,
                            audio_file=self.faulty_audio_file_unprocessed_object_key,
                            is_banned=False,
                        )
                    )

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clips...')

        originator_audio_clips = AudioClips.objects.bulk_create(originator_audio_clips, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        #cache

        stopwatch.start()
        print('Creating cache for users...')

        for audio_clip in originator_audio_clips:

            if audio_clip.generic_status.generic_status_name == 'processing_pending':

                continue

            target_cache_key = CreateAudioClips.determine_processing_cache_key(
                user_id=audio_clip.user.id,
            )
            target_cache = cache.get(target_cache_key, None)
            if target_cache is None:
                target_cache = CreateAudioClips.get_default_processing_cache_per_user()
            target_cache['processings'].update({
                str(audio_clip.id): CreateAudioClips.get_default_processing_object(
                    event=audio_clip.event,
                    audio_clip=audio_clip,
                ),
            })
            target_cache['processings'][str(audio_clip.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
            target_cache['processings'][str(audio_clip.id)]['status'] = audio_clip.generic_status.generic_status_name
            cache.set(target_cache_key, target_cache)

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clip_metrics...')

        for audio_clip in originator_audio_clips:

            originator_audio_clip_metrics.append(
                AudioClipMetrics(
                    audio_clip=audio_clip,
                    like_count=0,
                    dislike_count=0,
                    like_ratio=0,
                )
            )

        originator_audio_clip_metrics = AudioClipMetrics.objects.bulk_create(originator_audio_clip_metrics, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        return {
            'events': events,
            'originator_audio_clips': originator_audio_clips,
            'originator_audio_clip_metrics': originator_audio_clip_metrics,
        }


    #responder can only have 1 row of any processing/processing_pending/processing_failed
    #hence, proper RealisticBulkData.processing_scenarios is applied
    #i.e. can have users with 0 responder row of any processing/processing_pending/processing_failed
    def create_processing_responders(self, user_type:Literal['main', 'filler']):

        #OLD SOLUTION
            #-1 self.processing_scenarios for lower target_event_quantity, just no rows created for "no row" users, skip responder loop
            #this is rigid coding, and disrespects source of truth
        #NEW SOLUTION
            #just follow self.minimum_main_users_per_set, skip event for "no row" users
            #more consistent and reliable, easier to code

        #each user can only be replying to one event at any time
        #this quantity shall freely fulfill both main/filler user_type
        target_event_quantity = self.minimum_main_user_quantity

        #filler originators
        #every event must have unique responder
        originators = []
        responders = []

        if user_type == 'main':

            #fill only
            originators = self.create_new_users(
                user_quantity=len(self.main_users),
                user_type='filler'
            )

            #amount already accounted for via self.processing_scenarios
            responders = self.main_users

        else:

            #fill to target_event_quantity
            originators = self.create_new_users(
                user_quantity=target_event_quantity,
                user_type='filler'
            )

            #fill at one user for one responder
            responders = self.create_new_users(
                user_quantity=target_event_quantity,
                user_type='filler'
            )

        events = []
        originator_audio_clips = []
        originator_audio_clip_metrics = []
        responder_audio_clips = []
        responder_audio_clip_metrics = []
        event_reply_queues = []

        stopwatch = Stopwatch()

        print_with_function_name(f"Started.")
        stopwatch.start()

        #due to block * processing scenarios, the processing scenarios goes as 0123->0123

        #create originator+event first

        for originator in originators:

            #events must exist in db first before audio_clips, so we create them here
            events.append(
                EventsFactory(
                    event_created_by=originator,
                    event_generic_status_generic_status_name='incomplete',
                )
            )

            #randomise tone just because it's easier to code
            audio_clip_tone_index = random.randint(0, (len(self.audio_clip_tones) - 1))

            #for benchmarks, excluded tones must be left alone
            while audio_clip_tone_index in self.excluded_audio_clip_tones_indexes:

                #reroll
                audio_clip_tone_index = random.randint(0, (len(self.audio_clip_tones) - 1))

            audio_clip_tone = self.audio_clip_tones[audio_clip_tone_index]

            originator_audio_clips.append(
                AudioClips(
                    user=events[-1].created_by,
                    audio_clip_role=self.audio_clip_roles['originator'],
                    audio_clip_tone=audio_clip_tone,
                    event=events[-1],
                    generic_status=self.generic_statuses['ok'],
                    audio_file=self.audio_file,
                    audio_duration_s=self.audio_duration_s,
                    audio_volume_peaks=self.audio_volume_peaks,
                    is_banned=False,
                )
            )

        #now for responder, use index to loop processing scenarios

        processing_index = 0
        responder_index = 0

        processing_index_to_skip = self.processing_scenarios.index(None)

        for event in events:

            #since it's block*processing, user for processing_scenarios is going 0123 0123, so only need to skip 1 event at a time
            if processing_index == processing_index_to_skip:

                responder_index += 1
                processing_index = 0

                continue

            #randomise tone just because it's easier to code

            audio_clip_tone_index = random.randint(0, (len(self.audio_clip_tones) - 1))

            #for benchmarks, excluded tones must be left alone
            while audio_clip_tone_index in self.excluded_audio_clip_tones_indexes:

                #reroll
                audio_clip_tone_index = random.randint(0, (len(self.audio_clip_tones) - 1))

            audio_clip_tone = self.audio_clip_tones[audio_clip_tone_index]

            event_reply_queues.append(
                EventReplyQueues(
                    event=event,
                    locked_for_user=responders[responder_index],
                    is_replying=True,
                )
            )

            responder_audio_clips.append(
                AudioClips(
                    user=responders[responder_index],
                    audio_clip_role=self.audio_clip_roles['responder'],
                    audio_clip_tone=audio_clip_tone,
                    event=event,
                    generic_status=self.processing_scenarios[processing_index],
                    audio_file=self.faulty_audio_file_unprocessed_object_key,
                    is_banned=False,
                )
            )

            responder_index += 1
            processing_index += 1

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        #queues

        stopwatch.start()
        print('Creating event_reply_queues...')

        event_reply_queues = EventReplyQueues.objects.bulk_create(event_reply_queues, batch_size=self.db_batch_size)

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        #audio_clips

        stopwatch.start()
        print('Creating audio_clips...')

        originator_audio_clips = AudioClips.objects.bulk_create(originator_audio_clips, batch_size=self.db_batch_size)
        responder_audio_clips = AudioClips.objects.bulk_create(responder_audio_clips, batch_size=self.db_batch_size)
        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        #cache

        stopwatch.start()
        print('Creating cache for users...')

        for audio_clip in responder_audio_clips:

            if audio_clip.generic_status.generic_status_name == 'processing_pending':

                continue

            target_cache_key = CreateAudioClips.determine_processing_cache_key(
                user_id=audio_clip.user.id,
            )
            target_cache = cache.get(target_cache_key, None)
            if target_cache is None:
                target_cache = CreateAudioClips.get_default_processing_cache_per_user()
            target_cache['processings'].update({
                str(audio_clip.id): CreateAudioClips.get_default_processing_object(
                    event=audio_clip.event,
                    audio_clip=audio_clip,
                ),
            })
            target_cache['processings'][str(audio_clip.id)]['attempts_left'] = settings.AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS - 1
            target_cache['processings'][str(audio_clip.id)]['status'] = audio_clip.generic_status.generic_status_name
            cache.set(target_cache_key, target_cache)

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        stopwatch.start()
        print('Creating audio_clip_metrics...')

        for audio_clip in originator_audio_clips:

            originator_audio_clip_metrics.append(
                AudioClipMetrics(
                    audio_clip=audio_clip,
                    like_count=0,
                    dislike_count=0,
                    like_ratio=0,
                )
            )

        originator_audio_clip_metrics = AudioClipMetrics.objects.bulk_create(originator_audio_clip_metrics, batch_size=self.db_batch_size)

        reset_queries()

        for audio_clip in responder_audio_clips:

            responder_audio_clip_metrics.append(
                AudioClipMetrics(
                    audio_clip=audio_clip,
                    like_count=0,
                    dislike_count=0,
                    like_ratio=0,
                )
            )

        responder_audio_clip_metrics = AudioClipMetrics.objects.bulk_create(responder_audio_clip_metrics, batch_size=self.db_batch_size)

        reset_queries()

        stopwatch.stop()
        stopwatch.print_pretty_difference()

        return {
            'events': events,
            'originator_audio_clips': originator_audio_clips,
            'originator_audio_clip_metrics': originator_audio_clip_metrics,
            'event_reply_queues': event_reply_queues,
            'responder_audio_clips': responder_audio_clips,
            'responder_audio_clip_metrics': responder_audio_clip_metrics,
        }


    #just call this once for entire db, delete in db and recreate if .sample_run() is called again
    #simplicity is preferred here
    def create_user_blocks(self):

        #to avoid insane scaling when using entire db of users, we use only what self.get_main_users_relative_to_entire_db() gives

        #so we go block*processing -> classify those users into block scenarios

        is_blocking_users = []
        is_blocked_users = []

        for set_name in self.main_user_sets:

            user_index = 0

            for block_scenario in self.user_block_scenarios:

                if block_scenario is None:

                    break

                elif block_scenario == 'blocking':

                    for processing_scenario in self.processing_scenarios:

                        is_blocking_users.append(self.main_user_sets[set_name][user_index])

                        user_index += 1

                elif block_scenario == 'blocked':

                    for processing_scenario in self.processing_scenarios:

                        is_blocked_users.append(self.main_user_sets[set_name][user_index])

                        user_index += 1

                elif block_scenario == 'mutual_block':

                    for processing_scenario in self.processing_scenarios:

                        is_blocking_users.append(self.main_user_sets[set_name][user_index])
                        is_blocked_users.append(self.main_user_sets[set_name][user_index])

                        user_index += 1

                else:

                    raise ValueError(f'invalid {block_scenario}')

        #start

        user_blocks = []

        for user_a in is_blocking_users:

            for user_b in is_blocked_users:

                if user_a.id == user_b.id:

                    #cannot block yourself
                    continue

                user_blocks.append(
                    UserBlocks(user=user_a, blocked_user=user_b)
                )

        #delete rows in db to recreate according to latest version of db

        UserBlocks.objects.all().delete()

        #create
        #rely on unique constraint and ignore_conflicts=True to remove duplicates

        return UserBlocks.objects.bulk_create(user_blocks, ignore_conflicts=True, batch_size=self.db_batch_size)


    #if you want more rows, specify max_randomness_iteration_count
        #1 is just enough for other tests
    #cmd:
        #python manage.py shell -c "from voicewake.tests.test_metrics import RealisticBulkData; RealisticBulkData.sample_run(5, True);"
    @staticmethod
    def sample_run(max_randomness_iteration_count=1, use_threads=True):

        #add anything here for rows to be "earlier", beneficial for tests

        #user * blocks * blocked * is_originator(many/few/0) * is_responder(many/few/0)
        #ensure these special users are identifiable and retrievable, via username/email

        #this improves realism of randomness
        current_randomness_iteration_count = 0

        realistic_bulk_data_class = RealisticBulkData(
            db_batch_size=500,
        )

        while current_randomness_iteration_count < max_randomness_iteration_count:

            #create users per while-loop for realistic non-hyperactive users
            #filler users are automatically created within instance functions as one-off users
            realistic_bulk_data_class.create_new_users(user_type='main')

            realistic_bulk_data_class.prepare_like_dislike_estimate()

            if use_threads is False:

                #use this for TestCase to check that sample_run() is ok

                realistic_bulk_data_class.create_event_incomplete(True,)
                realistic_bulk_data_class.create_event_incomplete(False,)

                realistic_bulk_data_class.create_event_completed()
                realistic_bulk_data_class.create_event_completed()

                realistic_bulk_data_class.create_event_deleted(True, True, False,)
                realistic_bulk_data_class.create_event_deleted(True, False, True,)
                realistic_bulk_data_class.create_event_deleted(True, True, True,)

                realistic_bulk_data_class.create_event_deleted(False, True,)

                #call once only for every user
                queue_is_replying = random.randint(0, 1) == 1
                realistic_bulk_data_class.create_event_incomplete_and_event_reply_queue(queue_is_replying,)

                #users are not shared in these cases
                realistic_bulk_data_class.create_processing_originators(user_type='filler')
                realistic_bulk_data_class.create_processing_responders(user_type='filler')

                #since not reusing users, create their processings now
                realistic_bulk_data_class.create_processing_originators(user_type='main')
                realistic_bulk_data_class.create_processing_responders(user_type='main')

            else:

                threads = []

                threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_incomplete, args=(True,)))
                threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_incomplete, args=(False,)))

                threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_completed))
                threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_completed))

                threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_deleted, args=(True, True, False,)))
                threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_deleted, args=(True, False, True,)))
                threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_deleted, args=(True, True, True,)))

                threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_deleted, args=(False, True,)))

                #call once only for every user
                queue_is_replying = random.randint(0, 1) == 1
                threads.append(threading.Thread(target=realistic_bulk_data_class.create_event_incomplete_and_event_reply_queue, args=(queue_is_replying,)))

                #users are not shared in these cases
                threads.append(threading.Thread(target=realistic_bulk_data_class.create_processing_originators, args=('filler',)))
                threads.append(threading.Thread(target=realistic_bulk_data_class.create_processing_responders, args=('filler',)))

                #since not reusing users, create their processings now
                threads.append(threading.Thread(target=realistic_bulk_data_class.create_processing_originators, args=('main',)))
                threads.append(threading.Thread(target=realistic_bulk_data_class.create_processing_responders, args=('main',)))

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

            #GMT+8 for MY time
            print((get_datetime_now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S') + ': Done with one while-loop.')

            current_randomness_iteration_count += 1

        #blocks, only perform after everything to ensure no new users come after
        realistic_bulk_data_class.create_user_blocks()












@override_settings(
    DEBUG=True,
    EVENT_QUANTITY_PER_PAGE=4, #for faster tests
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
        for user in realistic_bulk_data_class.main_users:
            print(user.username)
            print(AudioClipLikesDislikes.objects.filter(user=user, is_liked=True).count())
            print(AudioClipLikesDislikes.objects.filter(user=user, is_liked=False).count())


    def test_realistic_bulk_data__determine_audio_clip_tones(self):

        realistic_bulk_data_class = RealisticBulkData()


    def test_realistic_bulk_data__create_users__mixed(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.create_new_users(user_type='main')
        realistic_bulk_data_class.create_new_users(user_type='filler')
        realistic_bulk_data_class.create_new_users(user_type='main')
        realistic_bulk_data_class.create_new_users(user_type='filler')


    def test_realistic_bulk_data__get_main_users_relative_to_entire_db(self):

        realistic_bulk_data_class = RealisticBulkData()

        #round 0
        #do create_new_users() and get_main_users_relative_to_entire_db()
        #expect exact match

        realistic_bulk_data_class.create_new_users(user_type='main')

        main_users_created_0 = realistic_bulk_data_class.main_users.copy()
        main_user_sets_created_0 = realistic_bulk_data_class.main_user_sets.copy()

        result = RealisticBulkData.get_main_users_relative_to_entire_db()

        main_users_get_0 = result['main_users']
        main_user_sets_get_0 = result['main_user_sets']

        #compare lengths of full lists
        self.assertEqual(len(main_users_created_0), realistic_bulk_data_class.minimum_main_user_quantity)
        self.assertEqual(len(main_users_get_0), realistic_bulk_data_class.minimum_main_user_quantity)

        #compare if full lists are matching via user ids
        for x in range(len(main_users_created_0)):

            self.assertEqual(main_users_created_0[x].id, main_users_get_0[x].id)

        for set_name in realistic_bulk_data_class.main_user_sets:

            #compare length of sets
            self.assertEqual(len(main_user_sets_created_0[set_name]), realistic_bulk_data_class.minimum_main_users_per_set)
            self.assertEqual(len(main_user_sets_get_0[set_name]), realistic_bulk_data_class.minimum_main_users_per_set)

            #compare user ids inside sets
            for x in range(realistic_bulk_data_class.minimum_main_users_per_set):

                self.assertEqual(main_user_sets_created_0[set_name][x].id, main_user_sets_get_0[set_name][x].id)

        #round 1
        #do create_new_users() and get_main_users_relative_to_entire_db()
        #expect earliest set to match, middle/latest to not match

        realistic_bulk_data_class.create_new_users(user_type='main')

        main_users_created_1 = realistic_bulk_data_class.main_users.copy()
        main_user_sets_created_1 = realistic_bulk_data_class.main_user_sets.copy()

        result = RealisticBulkData.get_main_users_relative_to_entire_db()

        main_users_get_1 = result['main_users']
        main_user_sets_get_1 = result['main_user_sets']

        #compare lengths of full lists
        self.assertEqual(len(main_users_created_0), realistic_bulk_data_class.minimum_main_user_quantity)
        self.assertEqual(len(main_users_get_0), realistic_bulk_data_class.minimum_main_user_quantity)

        for set_name in realistic_bulk_data_class.main_user_sets:

            #compare length of sets
            self.assertEqual(len(main_user_sets_created_0[set_name]), realistic_bulk_data_class.minimum_main_users_per_set)
            self.assertEqual(len(main_user_sets_get_0[set_name]), realistic_bulk_data_class.minimum_main_users_per_set)

        #check each user in full list, which for earliest, will match
        for x in range(realistic_bulk_data_class.minimum_main_users_per_set):

            self.assertEqual(main_users_get_0[x].id, main_users_get_1[x].id)

        #check each user in full list, which for middle/latest, will not match
        for x in range(realistic_bulk_data_class.minimum_main_users_per_set, len(main_users_get_0)):

            self.assertLess(main_users_get_0[x].id, main_users_get_1[x].id)

        #check each user in sets, which for earliest, will match everything
        for x in range(realistic_bulk_data_class.minimum_main_users_per_set):

            self.assertEqual(main_user_sets_get_0['earliest'][x].id, main_user_sets_get_1['earliest'][x].id)

        #check each user in sets, which for middle/latest, will not match
        for x in range(realistic_bulk_data_class.minimum_main_users_per_set):

            #check sets within each round
            self.assertLess(main_user_sets_get_0['earliest'][x].id, main_user_sets_get_0['middle'][x].id)
            self.assertLess(main_user_sets_get_0['middle'][x].id, main_user_sets_get_0['latest'][x].id)
            self.assertLess(main_user_sets_get_1['earliest'][x].id, main_user_sets_get_1['middle'][x].id)
            self.assertLess(main_user_sets_get_1['middle'][x].id, main_user_sets_get_1['latest'][x].id)

            #check sets between both rounds
            self.assertLess(main_user_sets_get_0['middle'][x].id, main_user_sets_get_1['middle'][x].id)
            self.assertLess(main_user_sets_get_0['latest'][x].id, main_user_sets_get_1['latest'][x].id)

        #since there are more sets now, check things across entire db

        all_users = realistic_bulk_data_class.main_user_group.user_set.all().order_by('id')
        set_quantity = len(all_users) / realistic_bulk_data_class.minimum_main_users_per_set

        #check if set count in db is consistent
        self.assertEqual(len(all_users) % realistic_bulk_data_class.minimum_main_users_per_set, 0)
        self.assertEqual(set_quantity, len(realistic_bulk_data_class.main_user_sets) * 2)

        #check if true middle set is accurate
        #use floor to adjust to 0-based index
        middle_set_first_user = math.floor(set_quantity / 2) * realistic_bulk_data_class.minimum_main_users_per_set
        middle_set_first_user = all_users[middle_set_first_user]

        self.assertEqual(
            middle_set_first_user.id,
            main_user_sets_get_1['middle'][0].id
        )


    def test_realistic_bulk_data__event_incomplete(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.create_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()

        result = realistic_bulk_data_class.create_event_incomplete()

        self.assertGreater(len(result['events']), 0)
        self.assertGreater(len(result['originator_audio_clips']), 0)
        self.assertGreater(len(result['originator_audio_clip_metrics']), 0)
        self.assertEqual(len(result['user_events']), 0)

        self.assertEqual(len(result['events']), len(result['originator_audio_clips']))
        self.assertEqual(len(result['events']), len(result['originator_audio_clip_metrics']))

        self.assertEqual(result['events'][0].generic_status.generic_status_name, 'incomplete')
        self.assertEqual(result['events'][-1].generic_status.generic_status_name, 'incomplete')

        self.assertEqual(result['originator_audio_clips'][0].generic_status.generic_status_name, 'ok')
        self.assertEqual(result['originator_audio_clips'][-1].generic_status.generic_status_name, 'ok')

        self.assertEqual(result['originator_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['originator_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'originator')

        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['originator_audio_clips'][0], is_liked=True).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['originator_audio_clips'][0], is_liked=False).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['originator_audio_clips'][-1], is_liked=True).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['originator_audio_clips'][-1], is_liked=False).count(), 0)

        self.metrics.update({
            inspect.currentframe().f_code.co_name: {
                'originator_audio_clips': len(result['originator_audio_clips']),
                'originator_audio_clip_metrics': len(result['originator_audio_clip_metrics']),
                'user_events': len(result['user_events']),
            }
        })


    def test_realistic_bulk_data__event_incomplete__has_skipped(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.create_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()

        result = realistic_bulk_data_class.create_event_incomplete(
            skipped_by_users=True,
        )

        self.assertGreater(len(result['events']), 0)
        self.assertGreater(len(result['originator_audio_clips']), 0)
        self.assertGreater(len(result['originator_audio_clip_metrics']), 0)
        self.assertGreater(len(result['user_events']), 0)

        self.assertEqual(len(result['events']), len(result['originator_audio_clips']))
        self.assertEqual(len(result['events']), len(result['originator_audio_clip_metrics']))

        self.assertEqual(result['events'][0].generic_status.generic_status_name, 'incomplete')
        self.assertEqual(result['events'][-1].generic_status.generic_status_name, 'incomplete')

        self.assertEqual(result['originator_audio_clips'][0].generic_status.generic_status_name, 'ok')
        self.assertEqual(result['originator_audio_clips'][-1].generic_status.generic_status_name, 'ok')

        self.assertEqual(result['originator_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['originator_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'originator')

        #-1 since originator cannot skip own events
        self.assertEqual(
            len(result['user_events']),
            (
                (len(realistic_bulk_data_class.audio_clip_tones) - len(realistic_bulk_data_class.excluded_audio_clip_tones_indexes))
                * realistic_bulk_data_class.event_quantity
                * len(realistic_bulk_data_class.main_users)
                #-1 because we simply skip creation if originator == current_user
                * (len(realistic_bulk_data_class.main_users) - 1)
            )
        )

        self.metrics.update({
            inspect.currentframe().f_code.co_name: {
                'originator_audio_clips': len(result['originator_audio_clips']),
                'originator_audio_clip_metrics': len(result['originator_audio_clip_metrics']),
                'user_events': len(result['user_events']),
            }
        })


    def test_realistic_bulk_data__event_incomplete__queue_not_replying(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.create_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()

        result = realistic_bulk_data_class.create_event_incomplete_and_event_reply_queue(is_replying=False)

        self.assertGreater(len(result['events']), 0)
        self.assertGreater(len(result['event_reply_queues']), 0)
        self.assertGreater(len(result['originator_audio_clips']), 0)
        self.assertGreater(len(result['originator_audio_clip_metrics']), 0)

        self.assertEqual(len(result['events']), len(result['originator_audio_clips']))
        self.assertEqual(len(result['events']), len(result['originator_audio_clip_metrics']))
        self.assertEqual(len(result['events']), len(result['event_reply_queues']))

        self.assertEqual(result['events'][0].generic_status.generic_status_name, 'incomplete')
        self.assertEqual(result['events'][-1].generic_status.generic_status_name, 'incomplete')

        self.assertEqual(result['originator_audio_clips'][0].generic_status.generic_status_name, 'ok')
        self.assertEqual(result['originator_audio_clips'][-1].generic_status.generic_status_name, 'ok')

        self.assertEqual(result['originator_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['originator_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'originator')

        self.assertEqual(result['event_reply_queues'][0].is_replying, False)
        self.assertEqual(result['event_reply_queues'][-1].is_replying, False)

        self.metrics.update({
            inspect.currentframe().f_code.co_name: {
                'events': len(result['events']),
                'event_reply_queues': len(result['event_reply_queues']),
                'originator_audio_clips': len(result['originator_audio_clips']),
                'originator_audio_clip_metrics': len(result['originator_audio_clip_metrics']),
            }
        })


    def test_realistic_bulk_data__event_incomplete__queue_is_replying(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.create_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()

        result = realistic_bulk_data_class.create_event_incomplete_and_event_reply_queue(is_replying=True)

        self.assertGreater(len(result['events']), 0)
        self.assertGreater(len(result['event_reply_queues']), 0)
        self.assertGreater(len(result['originator_audio_clips']), 0)
        self.assertGreater(len(result['originator_audio_clip_metrics']), 0)

        self.assertEqual(len(result['events']), len(result['originator_audio_clips']))
        self.assertEqual(len(result['events']), len(result['originator_audio_clip_metrics']))
        self.assertEqual(len(result['events']), len(result['event_reply_queues']))

        self.assertEqual(result['events'][0].generic_status.generic_status_name, 'incomplete')
        self.assertEqual(result['events'][-1].generic_status.generic_status_name, 'incomplete')

        self.assertEqual(result['originator_audio_clips'][0].generic_status.generic_status_name, 'ok')
        self.assertEqual(result['originator_audio_clips'][-1].generic_status.generic_status_name, 'ok')

        self.assertEqual(result['originator_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['originator_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'originator')

        self.assertEqual(result['event_reply_queues'][0].is_replying, True)
        self.assertEqual(result['event_reply_queues'][-1].is_replying, True)

        self.metrics.update({
            inspect.currentframe().f_code.co_name: {
                'events': len(result['events']),
                'event_reply_queues': len(result['event_reply_queues']),
                'originator_audio_clips': len(result['originator_audio_clips']),
                'originator_audio_clip_metrics': len(result['originator_audio_clip_metrics']),
            }
        })


    def test_realistic_bulk_data__event_completed(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.create_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()

        result = realistic_bulk_data_class.create_event_completed()

        self.assertGreater(len(result['events']), 0)
        self.assertGreater(len(result['originator_audio_clips']), 0)
        self.assertGreater(len(result['originator_audio_clip_metrics']), 0)
        self.assertGreater(len(result['responder_audio_clips']), 0)
        self.assertGreater(len(result['responder_audio_clip_metrics']), 0)

        self.assertEqual(len(result['events']), len(result['originator_audio_clips']))
        self.assertEqual(len(result['events']), len(result['originator_audio_clip_metrics']))
        self.assertEqual(len(result['events']), len(result['responder_audio_clips']))
        self.assertEqual(len(result['events']), len(result['responder_audio_clip_metrics']))

        self.assertEqual(result['events'][0].generic_status.generic_status_name, 'completed')
        self.assertEqual(result['events'][-1].generic_status.generic_status_name, 'completed')

        self.assertEqual(result['originator_audio_clips'][0].generic_status.generic_status_name, 'ok')
        self.assertEqual(result['originator_audio_clips'][-1].generic_status.generic_status_name, 'ok')
        self.assertEqual(result['responder_audio_clips'][0].generic_status.generic_status_name, 'ok')
        self.assertEqual(result['responder_audio_clips'][-1].generic_status.generic_status_name, 'ok')

        self.assertEqual(result['originator_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['originator_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['responder_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'responder')
        self.assertEqual(result['responder_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'responder')

        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['originator_audio_clips'][0], is_liked=True).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['originator_audio_clips'][0], is_liked=False).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['originator_audio_clips'][-1], is_liked=True).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['originator_audio_clips'][-1], is_liked=False).count(), 0)

        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['responder_audio_clips'][0], is_liked=True).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['responder_audio_clips'][0], is_liked=False).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['responder_audio_clips'][-1], is_liked=True).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['responder_audio_clips'][-1], is_liked=False).count(), 0)

        self.metrics.update({
            inspect.currentframe().f_code.co_name: {
                'events': len(result['events']),
                'originator_audio_clips': len(result['originator_audio_clips']),
                'responder_audio_clips': len(result['responder_audio_clips']),
                'originator_audio_clip_metrics': len(result['originator_audio_clip_metrics']),
                'responder_audio_clip_metrics': len(result['responder_audio_clip_metrics']),
            }
        })


    def test_realistic_bulk_data__event_deleted__has_responder__originator_banned__responder_ok(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.create_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()

        result = realistic_bulk_data_class.create_event_deleted(
            has_responder=True,
            is_originator_banned=True,
            is_responder_banned=False,
        )

        self.assertGreater(len(result['events']), 0)
        self.assertGreater(len(result['originator_audio_clips']), 0)
        self.assertGreater(len(result['originator_audio_clip_metrics']), 0)
        self.assertGreater(len(result['responder_audio_clips']), 0)
        self.assertGreater(len(result['responder_audio_clip_metrics']), 0)

        self.assertEqual(len(result['events']), len(result['originator_audio_clips']))
        self.assertEqual(len(result['events']), len(result['originator_audio_clip_metrics']))
        self.assertEqual(len(result['events']), len(result['responder_audio_clips']))
        self.assertEqual(len(result['events']), len(result['responder_audio_clip_metrics']))

        self.assertEqual(result['events'][0].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['events'][-1].generic_status.generic_status_name, 'deleted')

        self.assertEqual(result['originator_audio_clips'][0].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['originator_audio_clips'][-1].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['originator_audio_clips'][0].is_banned, True)
        self.assertEqual(result['originator_audio_clips'][-1].is_banned, True)

        self.assertEqual(result['responder_audio_clips'][0].generic_status.generic_status_name, 'ok')
        self.assertEqual(result['responder_audio_clips'][-1].generic_status.generic_status_name, 'ok')
        self.assertEqual(result['responder_audio_clips'][0].is_banned, False)
        self.assertEqual(result['responder_audio_clips'][-1].is_banned, False)

        self.assertEqual(result['originator_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['originator_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['responder_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'responder')
        self.assertEqual(result['responder_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'responder')

        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['originator_audio_clips'][0], is_liked=True).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['originator_audio_clips'][0], is_liked=False).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['originator_audio_clips'][-1], is_liked=True).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['originator_audio_clips'][-1], is_liked=False).count(), 0)

        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['responder_audio_clips'][0], is_liked=True).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['responder_audio_clips'][0], is_liked=False).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['responder_audio_clips'][-1], is_liked=True).count(), 0)
        self.assertGreater(AudioClipLikesDislikes.objects.filter(audio_clip_id=result['responder_audio_clips'][-1], is_liked=False).count(), 0)

        self.metrics.update({
            inspect.currentframe().f_code.co_name: {
                'events': len(result['events']),
                'originator_audio_clips': len(result['originator_audio_clips']),
                'responder_audio_clips': len(result['responder_audio_clips']),
                'originator_audio_clip_metrics': len(result['originator_audio_clip_metrics']),
                'responder_audio_clip_metrics': len(result['responder_audio_clip_metrics']),
            }
        })


    def test_realistic_bulk_data__event_deleted__has_responder__originator_ok__responder_banned(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.create_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()

        result = realistic_bulk_data_class.create_event_deleted(
            has_responder=True,
            is_originator_banned=False,
            is_responder_banned=True,
        )

        self.assertGreater(len(result['events']), 0)
        self.assertGreater(len(result['originator_audio_clips']), 0)
        self.assertGreater(len(result['originator_audio_clip_metrics']), 0)
        self.assertGreater(len(result['responder_audio_clips']), 0)
        self.assertGreater(len(result['responder_audio_clip_metrics']), 0)

        self.assertEqual(len(result['events']), len(result['originator_audio_clips']))
        self.assertEqual(len(result['events']), len(result['originator_audio_clip_metrics']))
        self.assertEqual(len(result['events']), len(result['responder_audio_clips']))
        self.assertEqual(len(result['events']), len(result['responder_audio_clip_metrics']))

        self.assertEqual(result['events'][0].generic_status.generic_status_name, 'incomplete')
        self.assertEqual(result['events'][-1].generic_status.generic_status_name, 'incomplete')

        self.assertEqual(result['originator_audio_clips'][0].generic_status.generic_status_name, 'ok')
        self.assertEqual(result['originator_audio_clips'][-1].generic_status.generic_status_name, 'ok')
        self.assertEqual(result['originator_audio_clips'][0].is_banned, False)
        self.assertEqual(result['originator_audio_clips'][-1].is_banned, False)

        self.assertEqual(result['responder_audio_clips'][0].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['responder_audio_clips'][-1].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['responder_audio_clips'][0].is_banned, True)
        self.assertEqual(result['responder_audio_clips'][-1].is_banned, True)

        self.assertEqual(result['originator_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['originator_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['responder_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'responder')
        self.assertEqual(result['responder_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'responder')

        self.metrics.update({
            inspect.currentframe().f_code.co_name: {
                'events': len(result['events']),
                'originator_audio_clips': len(result['originator_audio_clips']),
                'responder_audio_clips': len(result['responder_audio_clips']),
                'originator_audio_clip_metrics': len(result['originator_audio_clip_metrics']),
                'responder_audio_clip_metrics': len(result['responder_audio_clip_metrics']),
            }
        })


    def test_realistic_bulk_data__event_deleted__has_responder__originator_banned__responder_banned(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.create_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()

        result = realistic_bulk_data_class.create_event_deleted(
            has_responder=True,
            is_originator_banned=True,
            is_responder_banned=True,
        )

        self.assertGreater(len(result['events']), 0)
        self.assertGreater(len(result['originator_audio_clips']), 0)
        self.assertGreater(len(result['originator_audio_clip_metrics']), 0)
        self.assertGreater(len(result['responder_audio_clips']), 0)
        self.assertGreater(len(result['responder_audio_clip_metrics']), 0)

        self.assertEqual(len(result['events']), len(result['originator_audio_clips']))
        self.assertEqual(len(result['events']), len(result['originator_audio_clip_metrics']))
        self.assertEqual(len(result['events']), len(result['responder_audio_clips']))
        self.assertEqual(len(result['events']), len(result['responder_audio_clip_metrics']))

        self.assertEqual(result['events'][0].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['events'][-1].generic_status.generic_status_name, 'deleted')

        self.assertEqual(result['originator_audio_clips'][0].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['originator_audio_clips'][-1].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['originator_audio_clips'][0].is_banned, True)
        self.assertEqual(result['originator_audio_clips'][-1].is_banned, True)

        self.assertEqual(result['responder_audio_clips'][0].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['responder_audio_clips'][-1].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['responder_audio_clips'][0].is_banned, True)
        self.assertEqual(result['responder_audio_clips'][-1].is_banned, True)

        self.assertEqual(result['originator_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['originator_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['responder_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'responder')
        self.assertEqual(result['responder_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'responder')

        self.metrics.update({
            inspect.currentframe().f_code.co_name: {
                'events': len(result['events']),
                'originator_audio_clips': len(result['originator_audio_clips']),
                'responder_audio_clips': len(result['responder_audio_clips']),
                'originator_audio_clip_metrics': len(result['originator_audio_clip_metrics']),
                'responder_audio_clip_metrics': len(result['responder_audio_clip_metrics']),
            }
        })


    def test_realistic_bulk_data__event_deleted__no_responder__originator_banned(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.create_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()

        result = realistic_bulk_data_class.create_event_deleted(
            has_responder=False,
            is_originator_banned=True,
            is_responder_banned=False,
        )

        self.assertGreater(len(result['events']), 0)
        self.assertGreater(len(result['originator_audio_clips']), 0)
        self.assertGreater(len(result['originator_audio_clip_metrics']), 0)
        self.assertEqual(len(result['responder_audio_clips']), 0)
        self.assertEqual(len(result['responder_audio_clip_metrics']), 0)

        self.assertEqual(len(result['events']), len(result['originator_audio_clips']))
        self.assertEqual(len(result['events']), len(result['originator_audio_clip_metrics']))

        self.assertEqual(result['events'][0].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['events'][-1].generic_status.generic_status_name, 'deleted')

        self.assertEqual(result['originator_audio_clips'][0].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['originator_audio_clips'][-1].generic_status.generic_status_name, 'deleted')
        self.assertEqual(result['originator_audio_clips'][0].is_banned, True)
        self.assertEqual(result['originator_audio_clips'][-1].is_banned, True)

        self.assertEqual(result['originator_audio_clips'][0].audio_clip_role.audio_clip_role_name, 'originator')
        self.assertEqual(result['originator_audio_clips'][-1].audio_clip_role.audio_clip_role_name, 'originator')

        self.metrics.update({
            inspect.currentframe().f_code.co_name: {
                'events': len(result['events']),
                'originator_audio_clips': len(result['originator_audio_clips']),
                'responder_audio_clips': len(result['responder_audio_clips']),
                'originator_audio_clip_metrics': len(result['originator_audio_clip_metrics']),
                'responder_audio_clip_metrics': len(result['responder_audio_clip_metrics']),
            }
        })


    def test_realistic_bulk_data__event_deleted__expected_failures(self):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.create_new_users()
        realistic_bulk_data_class.prepare_like_dislike_estimate()

        try:
            realistic_bulk_data_class.create_event_deleted(has_responder=False, is_originator_banned=False, is_responder_banned=False)
            raise ValueError('Expected to fail.')
        except:
            pass

        try:
            realistic_bulk_data_class.create_event_deleted(has_responder=False, is_originator_banned=True, is_responder_banned=True)
            raise ValueError('Expected to fail.')
        except:
            pass


    def test_realistic_bulk_data__processing_originators(self):

        #for each user
        events_per_user_per_processing_scenario = 2

        realistic_bulk_data_class = RealisticBulkData()

        for target_user_type in ['main', 'filler']:

            if target_user_type == 'main':

                #always use fresh main users
                realistic_bulk_data_class.create_new_users(user_type=target_user_type)

            #filler users are automatically created
            result = realistic_bulk_data_class.create_processing_originators(
                user_type=target_user_type,
                events_per_user_per_processing_scenario=events_per_user_per_processing_scenario
            )

            self.assertGreater(len(result['events']), 0)
            self.assertGreater(len(result['originator_audio_clips']), 0)
            self.assertGreater(len(result['originator_audio_clip_metrics']), 0)

            self.assertEqual(len(result['events']), len(result['originator_audio_clips']))
            self.assertEqual(len(result['events']), len(result['originator_audio_clip_metrics']))

            #looping through self.processing_scenarios like user_0:0123 user1:0123

            loop_index = 0

            #lazy way to allow first row to compare with something without needing if-statement
            compared_originator_id = result['originator_audio_clips'][0].user.id

            processing_scenario_index = 0
            processing_scenario_index_to_skip = realistic_bulk_data_class.processing_scenarios.index(None)

            row_count_per_processing_scenario = 0

            while loop_index < len(result['events']):

                #event
                self.assertEqual(result['events'][loop_index].generic_status.generic_status_name, 'processing')
                self.assertEqual(
                    result['events'][loop_index].created_by.id,
                    result['originator_audio_clips'][loop_index].user.id,
                )

                #condition to move on to next processing_scenario
                if row_count_per_processing_scenario == events_per_user_per_processing_scenario:

                    row_count_per_processing_scenario = 0
                    processing_scenario_index += 1

                #condition to reloop processing scenario
                if processing_scenario_index == processing_scenario_index_to_skip:

                    #None marks the end of current user, since it's user*processing, so user*0123
                    #there will be no rows when user is expected to have no processing, so reality is user_0*012, user_1*012, etc.

                    try:

                        #save next user for comparison
                        compared_originator_id = result['originator_audio_clips'][loop_index+1].user.id

                    except IndexError:

                        #end of list
                        break

                    #reset
                    processing_scenario_index = 0

                #since there's no such thing as "AudioClips.generic_status=None", we always proceed

                #originator
                self.assertEqual(
                    result['originator_audio_clips'][loop_index].generic_status.generic_status_name,
                    realistic_bulk_data_class.processing_scenarios[processing_scenario_index].generic_status_name
                )
                self.assertEqual(result['originator_audio_clips'][loop_index].audio_clip_role.audio_clip_role_name, 'originator')
                self.assertEqual(result['events'][loop_index].id, result['originator_audio_clips'][loop_index].event.id)

                #still same user, due to user*processing
                self.assertEqual(result['originator_audio_clips'][loop_index].user.id, compared_originator_id)

                if result['originator_audio_clips'][loop_index].generic_status.generic_status_name == 'processing_pending':

                    #no cache
                    target_cache = cache.get(
                        CreateAudioClips.determine_processing_cache_key(
                            user_id=result['originator_audio_clips'][loop_index].user.id
                        ),
                        None
                    )

                    if target_cache is not None:

                        processing_object = CreateAudioClips.get_processing_object_from_processing_cache(
                            target_cache,
                            result['originator_audio_clips'][loop_index].id
                        )
                        self.assertIsNone(processing_object)

                else:

                    #cache
                    target_cache = cache.get(
                        CreateAudioClips.determine_processing_cache_key(
                            user_id=result['originator_audio_clips'][loop_index].user.id
                        ),
                        None
                    )
                    processing_object = CreateAudioClips.get_processing_object_from_processing_cache(
                        target_cache,
                        result['originator_audio_clips'][loop_index].id
                    )
                    self.assertIsNotNone(processing_object)
                    self.assertEqual(
                        processing_object['status'],
                        result['originator_audio_clips'][loop_index].generic_status.generic_status_name
                    )
                    self.assertGreater(processing_object['attempts_left'], 0)

                row_count_per_processing_scenario += 1

                loop_index += 1

            self.metrics.update({
                f'{inspect.currentframe().f_code.co_name}__{target_user_type}': {
                    'events': len(result['events']),
                    'originator_audio_clips': len(result['originator_audio_clips']),
                    'originator_audio_clip_metrics': len(result['originator_audio_clip_metrics']),
                }
            })


    def test_realistic_bulk_data__processing_responders(self):

        realistic_bulk_data_class = RealisticBulkData()

        for target_user_type in ['main', 'filler']:

            if target_user_type == 'main':

                #always use fresh main users
                realistic_bulk_data_class.create_new_users(user_type=target_user_type)

            #filler users are automatically created
            result = realistic_bulk_data_class.create_processing_responders(user_type=target_user_type)

            self.assertGreater(len(result['events']), 0)
            self.assertGreater(len(result['originator_audio_clips']), 0)
            self.assertGreater(len(result['originator_audio_clip_metrics']), 0)
            self.assertGreater(len(result['event_reply_queues']), 0)
            self.assertGreater(len(result['originator_audio_clips']), 0)
            self.assertGreater(len(result['originator_audio_clip_metrics']), 0)

            self.assertEqual(len(result['events']), len(result['originator_audio_clips']))
            self.assertEqual(len(result['events']), len(result['originator_audio_clip_metrics']))
            self.assertGreater(len(result['events']), len(result['event_reply_queues']))
            self.assertGreater(len(result['events']), len(result['responder_audio_clips']))
            self.assertGreater(len(result['events']), len(result['responder_audio_clip_metrics']))

            #every row is continuously looping through self.processing_scenarios like 0123 0123, and every responder is a different user
            #if responder is supposed to have no processing, originator will exist but not responder

            loop_index = 0

            responder_index = 0

            #lazy way to allow first row to compare with something without needing if-statement
            previous_responder_id = 0

            processing_scenario_index = 0
            processing_scenario_index_to_skip = realistic_bulk_data_class.processing_scenarios.index(None)

            while loop_index < len(result['events']):

                #event
                self.assertEqual(result['events'][loop_index].generic_status.generic_status_name, 'incomplete')
                self.assertEqual(
                    result['events'][loop_index].created_by.id,
                    result['originator_audio_clips'][loop_index].user.id,
                )

                #originator
                self.assertEqual(result['originator_audio_clips'][loop_index].generic_status.generic_status_name, 'ok')
                self.assertEqual(result['originator_audio_clips'][loop_index].audio_clip_role.audio_clip_role_name, 'originator')

                #responder+queue

                if processing_scenario_index == processing_scenario_index_to_skip:

                    #no responder+queue

                    self.assertFalse(
                        EventReplyQueues.objects.filter(event=result['events'][loop_index]).exists()
                    )
                    self.assertFalse(
                        AudioClips.objects.filter(
                            event=result['events'][loop_index],
                            audio_clip_role__audio_clip_role_name='responder',
                        ).exists()
                    )
                    self.assertFalse(
                        AudioClips.objects.filter(
                            event=result['events'][loop_index],
                            user=realistic_bulk_data_class.main_users[responder_index]
                        ).exists()
                    )

                    #do not increment responder_index here
                    #when this event has no responder, current responder is meant for next event

                    processing_scenario_index = 0

                else:

                    #has responder+queue

                    #queue
                    self.assertEqual(
                        result['responder_audio_clips'][responder_index].user.id,
                        result['event_reply_queues'][responder_index].locked_for_user.id,
                    )
                    self.assertEqual(result['event_reply_queues'][responder_index].is_replying, True)
                    self.assertEqual(result['event_reply_queues'][responder_index].event.id, result['events'][loop_index].id)

                    #responder
                    #every responder's user id will increment
                    self.assertEqual(
                        result['responder_audio_clips'][responder_index].event.id,
                        result['events'][loop_index].id
                    )
                    self.assertEqual(
                        result['responder_audio_clips'][responder_index].generic_status.generic_status_name,
                        realistic_bulk_data_class.processing_scenarios[processing_scenario_index].generic_status_name
                    )
                    self.assertEqual(
                        result['responder_audio_clips'][responder_index].audio_clip_role.audio_clip_role_name,
                        'responder'
                    )
                    self.assertGreater(
                        result['responder_audio_clips'][responder_index].user.id,
                        previous_responder_id
                    )

                    if result['responder_audio_clips'][responder_index].generic_status.generic_status_name == 'processing_pending':

                        #no cache

                        target_cache = cache.get(
                            CreateAudioClips.determine_processing_cache_key(
                                user_id=result['responder_audio_clips'][responder_index].user.id
                            ),
                            None
                        )

                        if target_cache is not None:

                            processing_object = CreateAudioClips.get_processing_object_from_processing_cache(
                                target_cache,
                                result['responder_audio_clips'][responder_index].id
                            )
                            self.assertIsNone(processing_object)

                    else:

                        #cache

                        target_cache = cache.get(
                            CreateAudioClips.determine_processing_cache_key(
                                user_id=result['responder_audio_clips'][responder_index].user.id
                            ),
                            None
                        )
                        processing_object = CreateAudioClips.get_processing_object_from_processing_cache(
                            target_cache,
                            result['responder_audio_clips'][responder_index].id
                        )
                        self.assertIsNotNone(processing_object)
                        self.assertEqual(
                            processing_object['status'],
                            result['responder_audio_clips'][responder_index].generic_status.generic_status_name
                        )
                        self.assertGreater(processing_object['attempts_left'], 0)

                    previous_responder_id = result['responder_audio_clips'][responder_index].user.id

                    processing_scenario_index += 1
                    responder_index += 1

                loop_index += 1

            self.metrics.update({
                f'{inspect.currentframe().f_code.co_name}__{target_user_type}': {
                    'events': len(result['events']),
                    'originator_audio_clips': len(result['originator_audio_clips']),
                    'originator_audio_clip_metrics': len(result['originator_audio_clip_metrics']),
                    'event_reply_queues': len(result['event_reply_queues']),
                    'responder_audio_clips': len(result['responder_audio_clips']),
                    'responder_audio_clip_metrics': len(result['responder_audio_clip_metrics']),
                }
            })


    def test_realistic_bulk_data__user_blocks(self):

        realistic_bulk_data_class = RealisticBulkData()

        #always use fresh main users
        realistic_bulk_data_class.create_new_users(user_type='main')

        user_blocks = realistic_bulk_data_class.create_user_blocks()

        #block*processing

        user_index = 0

        for user_block_scenario in realistic_bulk_data_class.user_block_scenarios:

            for processing_scenario in realistic_bulk_data_class.processing_scenarios:

                if user_block_scenario == 'blocking':

                    self.assertTrue(UserBlocks.objects.filter(user=realistic_bulk_data_class.main_users[user_index]).exists())
                    self.assertFalse(UserBlocks.objects.filter(blocked_user=realistic_bulk_data_class.main_users[user_index]).exists())

                elif user_block_scenario == 'blocked':

                    self.assertFalse(UserBlocks.objects.filter(user=realistic_bulk_data_class.main_users[user_index]).exists())
                    self.assertTrue(UserBlocks.objects.filter(blocked_user=realistic_bulk_data_class.main_users[user_index]).exists())

                elif user_block_scenario == 'mutual_block':

                    self.assertTrue(UserBlocks.objects.filter(user=realistic_bulk_data_class.main_users[user_index]).exists())
                    self.assertTrue(UserBlocks.objects.filter(blocked_user=realistic_bulk_data_class.main_users[user_index]).exists())

                elif user_block_scenario == None:

                    self.assertFalse(UserBlocks.objects.filter(user=realistic_bulk_data_class.main_users[user_index]).exists())
                    self.assertFalse(UserBlocks.objects.filter(blocked_user=realistic_bulk_data_class.main_users[user_index]).exists())

                user_index += 1












#separate sample_run() test because doing it every time you run RealisticBulkData_TestCase is unnecessary
@override_settings(
    DEBUG=True,
    EVENT_QUANTITY_PER_PAGE=4, #for faster tests
)
class RealisticBulkData_SampleRun_TestCase(TestCase):

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


    def test_realistic_bulk_data__small_sample_run(self):

        #first run
        RealisticBulkData.sample_run(max_randomness_iteration_count=1, use_threads=False,)

        #test repeated calls
        RealisticBulkData.sample_run(max_randomness_iteration_count=1, use_threads=False,)















#how to test:
    #build your data in local dev database (not test database), then run against it
    #test each test_() individually, as running all tests concurrently will have worse performance
#this test handles full validation and performance of apis.BrowseEvents
    #easier to do it here than to duplicate into test_apis and test_metrics
    #uses RealisticBulkData
#logic behaviours:
    #since we have cursor tokens, always test (latest->back/to), (earliest->back/to)
    #for tests that test on filtering, we iterate through list of filters in a single test case, else exponential
        #a test case for filters then becomes unique by differentiating into latest/earliest/empty rows to test db indexing
    #you may see a repeat queryset between audio_clip_tone_id and expected_rows
        #this is necessary so we can do [:1] and guarantee all expected_rows later only has the same audio_clip_tone
        #expected_rows on its own cannot guarantee that all rows have the same audio_clip_tone
#minimum_time_elapsed_ms
    #sometimes if db has no active caching, it will take nearly 300ms
        #after first test run and caching is done, it will be at optimal times of 50ms-150ms
@override_settings(
    DEBUG=True,
)
class BrowseEvents_TestCase(TestCase):

    #{test_function_name: anything}
    metrics = {}

    @classmethod
    def setUpTestData(cls):

        cls.realistic_bulk_data_class = RealisticBulkData()

        result = cls.realistic_bulk_data_class.get_main_users_relative_to_entire_db()
        cls.main_users = result['main_users']
        cls.main_user_sets = result['main_user_sets']


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


    #response_data['data']: [{event:event,originator:[],responder:[]}]
    def _general_row_check(self, response_data, api_kwargs, is_event_always_completed=True):

        audio_clip_role_name = api_kwargs['audio_clip_role_name']

        opposite_audio_clip_role_name = 'originator'

        if opposite_audio_clip_role_name == audio_clip_role_name:

            opposite_audio_clip_role_name = 'responder'

        if is_event_always_completed is True:

            #more straightforward

            previous_row = response_data['data'][0]

            #perform first check for precedence in the rest of the rows
            #all following rows must have the same values

            self.assertEqual(previous_row['event']['generic_status']['generic_status_name'], 'completed')
            self.assertEqual(previous_row[audio_clip_role_name][0]['audio_clip_role']['audio_clip_role_name'], audio_clip_role_name)
            self.assertEqual(previous_row[audio_clip_role_name][0]['generic_status']['generic_status_name'], 'ok')
            self.assertEqual(AudioClips.objects.values_list('is_banned', flat=True).get(pk=previous_row[audio_clip_role_name][0]['id']), False)
            self.assertEqual(previous_row[audio_clip_role_name][0]['event_id'], previous_row['event']['id'])

            self.assertEqual(previous_row[opposite_audio_clip_role_name][0]['audio_clip_role']['audio_clip_role_name'], opposite_audio_clip_role_name)
            self.assertEqual(previous_row[opposite_audio_clip_role_name][0]['generic_status']['generic_status_name'], 'ok')
            self.assertEqual(AudioClips.objects.values_list('is_banned', flat=True).get(pk=previous_row[opposite_audio_clip_role_name][0]['id']), False)
            self.assertEqual(previous_row[opposite_audio_clip_role_name][0]['event_id'], previous_row['event']['id'])

            for data_index in range(1, len(response_data['data'])):

                #just to occupy less space
                current_row = response_data['data'][data_index]

                #same role
                self.assertEqual(
                    current_row[audio_clip_role_name][0]['audio_clip_role']['id'],
                    previous_row[audio_clip_role_name][0]['audio_clip_role']['id'],
                )

                #cannot do assertLess for PK id
                #stumbled across larger PK id with smaller when_created
                #PK and now() are also never guaranteed, as threads can reserve ids before they're created

                #smaller or equal when_created
                self.assertLessEqual(
                    AudioClips.objects.values_list('when_created', flat=True,).get(
                        pk=current_row[audio_clip_role_name][0]['id']
                    ),
                    AudioClips.objects.values_list('when_created', flat=True,).get(
                        pk=previous_row[audio_clip_role_name][0]['id']
                    )
                )

                #general correctness

                self.assertEqual(current_row[audio_clip_role_name][0]['audio_clip_role']['audio_clip_role_name'], audio_clip_role_name)
                self.assertEqual(current_row[audio_clip_role_name][0]['generic_status']['generic_status_name'], 'ok')
                self.assertEqual(AudioClips.objects.values_list('is_banned', flat=True).get(pk=current_row[audio_clip_role_name][0]['id']), False)
                self.assertEqual(current_row[audio_clip_role_name][0]['event_id'], current_row['event']['id'])

                self.assertEqual(current_row[opposite_audio_clip_role_name][0]['audio_clip_role']['audio_clip_role_name'], opposite_audio_clip_role_name)
                self.assertEqual(current_row[opposite_audio_clip_role_name][0]['generic_status']['generic_status_name'], 'ok')
                self.assertEqual(AudioClips.objects.values_list('is_banned', flat=True).get(pk=current_row[opposite_audio_clip_role_name][0]['id']), False)
                self.assertEqual(current_row[opposite_audio_clip_role_name][0]['event_id'], current_row['event']['id'])

                previous_row = current_row

        else:

            #perform first check for precedence in the rest of the rows
            #all following rows must have the same values

            previous_row = response_data['data'][0]

            expected_is_liked = None

            if 'likes_or_dislikes' in api_kwargs:

                expected_is_liked = api_kwargs['likes_or_dislikes'] == 'likes'

            #at user page, like dislike page
                #incomplete/completed when originator
                #completed/deleted when responder

            if audio_clip_role_name == 'originator':

                self.assertIn(previous_row['event']['generic_status']['generic_status_name'], ['incomplete', 'completed'])

            else:

                self.assertIn(previous_row['event']['generic_status']['generic_status_name'], ['completed', 'deleted'])

            if expected_is_liked is None:

                #not like/dislike page
                self.assertEqual(previous_row[audio_clip_role_name][0]['user']['username'], api_kwargs['username'])

            else:

                #is like/dislike page
                self.assertEqual(previous_row[audio_clip_role_name][0]['is_liked_by_user'], expected_is_liked)

            self.assertEqual(previous_row[audio_clip_role_name][0]['audio_clip_role']['audio_clip_role_name'], audio_clip_role_name)
            self.assertEqual(previous_row[audio_clip_role_name][0]['generic_status']['generic_status_name'], 'ok')
            self.assertEqual(AudioClips.objects.values_list('is_banned', flat=True).get(pk=previous_row[audio_clip_role_name][0]['id']), False)
            self.assertEqual(previous_row[audio_clip_role_name][0]['event_id'], previous_row['event']['id'])

            if len(previous_row[opposite_audio_clip_role_name]) > 0:

                self.assertEqual(previous_row[opposite_audio_clip_role_name][0]['audio_clip_role']['audio_clip_role_name'], opposite_audio_clip_role_name)
                self.assertEqual(previous_row[opposite_audio_clip_role_name][0]['generic_status']['generic_status_name'], 'ok')
                self.assertEqual(AudioClips.objects.values_list('is_banned', flat=True).get(pk=previous_row[opposite_audio_clip_role_name][0]['id']), False)
                self.assertEqual(previous_row[opposite_audio_clip_role_name][0]['event_id'], previous_row['event']['id'])
    
            for data_index in range(1, len(response_data['data'])):
            
                #just to occupy less IDE space
                current_row = response_data['data'][data_index]
    
                #same role
                self.assertEqual(
                    current_row[audio_clip_role_name][0]['audio_clip_role']['id'],
                    previous_row[audio_clip_role_name][0]['audio_clip_role']['id'],
                )
    
                #cannot do assertLess for PK id
                #stumbled across larger PK id with smaller when_created
                #PK and now() are also never guaranteed, as threads can reserve ids before they're created
    
                #smaller or equal when_created
                self.assertLessEqual(
                    AudioClips.objects.values_list('when_created', flat=True,).get(
                        pk=current_row[audio_clip_role_name][0]['id']
                    ),
                    AudioClips.objects.values_list('when_created', flat=True,).get(
                        pk=previous_row[audio_clip_role_name][0]['id']
                    )
                )
    
                #general correctness

                if audio_clip_role_name == 'originator':

                    self.assertIn(current_row['event']['generic_status']['generic_status_name'], ['incomplete', 'completed'])

                else:

                    self.assertIn(current_row['event']['generic_status']['generic_status_name'], ['completed', 'deleted'])
    
                self.assertEqual(current_row[audio_clip_role_name][0]['audio_clip_role']['audio_clip_role_name'], audio_clip_role_name)
                self.assertEqual(current_row[audio_clip_role_name][0]['generic_status']['generic_status_name'], 'ok')
                self.assertEqual(AudioClips.objects.values_list('is_banned', flat=True).get(pk=current_row[audio_clip_role_name][0]['id']), False)
                self.assertEqual(current_row[audio_clip_role_name][0]['event_id'], current_row['event']['id'])

                if expected_is_liked is None:

                    #not like/dislike page
                    self.assertEqual(current_row[audio_clip_role_name][0]['user']['username'], api_kwargs['username'])

                else:

                    #is like/dislike page
                    self.assertEqual(current_row[audio_clip_role_name][0]['is_liked_by_user'], expected_is_liked)

                if len(current_row[opposite_audio_clip_role_name]) > 0:

                    self.assertEqual(current_row[opposite_audio_clip_role_name][0]['audio_clip_role']['audio_clip_role_name'], opposite_audio_clip_role_name)
                    self.assertEqual(current_row[opposite_audio_clip_role_name][0]['generic_status']['generic_status_name'], 'ok')
                    self.assertEqual(AudioClips.objects.values_list('is_banned', flat=True).get(pk=current_row[opposite_audio_clip_role_name][0]['id']), False)
                    self.assertEqual(current_row[opposite_audio_clip_role_name][0]['event_id'], current_row['event']['id'])
    
                previous_row = current_row


    def _general_cursor_token_check(self, response_data, audio_clip_role_name:Literal['originator','responder']):

        decoded_cursor_token = decode_cursor_token(response_data['next_token'])

        self.assertEqual(
            AudioClips.objects.values_list('when_created', flat=True,).get(
                pk=response_data['data'][-1][audio_clip_role_name][0]['id']
            ),
            get_datetime_from_string(decoded_cursor_token['when_created']),
        )
        self.assertEqual(
            response_data['data'][-1][audio_clip_role_name][0]['id'],
            decoded_cursor_token['id'],
        )

        decoded_cursor_token = decode_cursor_token(response_data['back_token'])

        self.assertEqual(
            AudioClips.objects.values_list('when_created', flat=True,).get(
                pk=response_data['data'][0][audio_clip_role_name][0]['id']
            ),
            get_datetime_from_string(decoded_cursor_token['when_created']),
        )
        self.assertEqual(
            response_data['data'][0][audio_clip_role_name][0]['id'],
            decoded_cursor_token['id'],
        )


    def _like_dislike_cursor_token_check(self, response_data, audio_clip_role_name:Literal['originator','responder'], unique_user):

        decoded_cursor_token = decode_cursor_token(response_data['next_token'])

        target_audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(
            audio_clip_id=response_data['data'][-1][audio_clip_role_name][0]['id'],
            user=unique_user,
        )

        self.assertEqual(
            target_audio_clip_like_dislike.last_modified,
            get_datetime_from_string(decoded_cursor_token['last_modified']),
        )
        self.assertEqual(
            target_audio_clip_like_dislike.id,
            decoded_cursor_token['id'],
        )

        decoded_cursor_token = decode_cursor_token(response_data['back_token'])

        target_audio_clip_like_dislike = AudioClipLikesDislikes.objects.get(
            audio_clip_id=response_data['data'][0][audio_clip_role_name][0]['id'],
            user=unique_user,
        )

        self.assertEqual(
            target_audio_clip_like_dislike.last_modified,
            get_datetime_from_string(decoded_cursor_token['last_modified']),
        )
        self.assertEqual(
            target_audio_clip_like_dislike.id,
            decoded_cursor_token['id'],
        )


    def test_browse_events__main_page(self, minimum_time_elapsed_ms=300, skip_to_loop=None):

        stopwatch = Stopwatch()

        #create all possible test cases

        #{'api_kwargs': {}, 'test_values': {}}
        test_cases = []

        #need to test all users, since some users can have 0 rows
        for login_user in self.main_users:

            for audio_clip_role_name in ['originator', 'responder']:

                #add "no audio_clip_tone selected"
                current_kwargs = {
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': audio_clip_role_name,
                    'next_or_back': 'next',
                }

                test_cases.append({
                    'api_kwargs': current_kwargs,
                    'test_values': {
                        'is_excluded_audio_clip_tone': False,
                        'login_user': login_user,
                        'target_user': None,
                    }
                })

                #others
                for audio_clip_tone_index, audio_clip_tone in enumerate(self.realistic_bulk_data_class.audio_clip_tones):

                    is_excluded_audio_clip_tone = audio_clip_tone_index in self.realistic_bulk_data_class.excluded_audio_clip_tones_indexes

                    current_kwargs = {
                        'latest_or_best': 'latest',
                        'timeframe': 'all',
                        'audio_clip_role_name': audio_clip_role_name,
                        'next_or_back': 'next',
                        'audio_clip_tone_id': audio_clip_tone.id,
                    }

                    test_cases.append({
                        'api_kwargs': current_kwargs,
                        'test_values': {
                            'is_excluded_audio_clip_tone': is_excluded_audio_clip_tone,
                            'login_user': login_user,
                            'target_user': None,
                        }
                    })

        #start test

        #use this to skip directly to problematic test
        skip_to_index = 0

        for test_index, test_case in enumerate(test_cases):

            if test_index < skip_to_index:

                print(f'Skipping test #{test_index} towards #{skip_to_index}.')
                continue

            #some queries on first run will cause delay due to lack of caching at db
            #if exceeding minimum_time_elapsed_ms, retry once

            login_user = test_case['test_values']['login_user']
            target_user = test_case['test_values']['target_user']
            audio_clip_role_name = test_case['api_kwargs']['audio_clip_role_name']
            is_excluded_audio_clip_tone = test_case['test_values']['is_excluded_audio_clip_tone']

            self.login(login_user)

            retries_left = 1

            while retries_left >= 0:

                #unpack test_case

                #must .copy() so retrying will not reuse cursor and exceed rows available
                current_kwargs = test_case['api_kwargs'].copy()

                try:

                    loop_title = 'loop #' + str(test_index)

                    print(loop_title)

                    if skip_to_loop is not None and test_index != skip_to_loop:

                        break

                    #========================================
                    #part 1: from latest audio_clip
                    #========================================

                    #==========
                    #API next
                    #==========

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    #if using excluded audio_clip_tone, always no rows
                    #skip to next test case
                    if is_excluded_audio_clip_tone is True:

                        self.assertEqual(len(response_data['data']), 0)
                        break

                    self.assertGreater(len(response_data['data']), 0)

                    #check rows
                    self._general_row_check(response_data, current_kwargs)

                    #keep this for next->back validation later
                    first_response_data = response_data['data'].copy()

                    #check tokens
                    self._general_cursor_token_check(response_data, audio_clip_role_name)

                    #==========
                    #API next+token
                    #==========

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': response_data['next_token'],
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    self.assertGreater(len(response_data['data']), 0)

                    #check rows
                    self._general_row_check(response_data, current_kwargs)

                    #check tokens
                    self._general_cursor_token_check(response_data, audio_clip_role_name)

                    #==========
                    #API back+token
                    #==========

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

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    #check rows
                    self._general_row_check(response_data, current_kwargs)

                    #check tokens
                    self._general_cursor_token_check(response_data, audio_clip_role_name)

                    #ensure everything is the same as first response

                    self.assertEqual(len(response_data['data']), len(first_response_data))

                    for index in range(len(response_data['data'])):

                        self.assertEqual(
                            response_data['data'][index]['originator'][0]['id'],
                            first_response_data[index]['originator'][0]['id'],
                        )
                        self.assertEqual(
                            response_data['data'][index]['responder'][0]['id'],
                            first_response_data[index]['responder'][0]['id'],
                        )

                    #==========
                    #API back+token again, expect no rows
                    #==========

                    cursor_token = response_data['back_token']

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

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #next_token, back_token, data
                    response_data = get_response_data(request)

                    self.assertEqual(len(response_data['data']), 0)
                    self.assertEqual(response_data['next_token'], response_data['back_token'])
                    self.assertEqual(response_data['next_token'], cursor_token)

                    #========================================
                    #part 2: from earliest audio_clip
                    #========================================

                    #==========
                    #API next with last row in db, expect 0 rows
                    #==========

                    #construct our own cursor from earliest eligible audio_clip

                    earliest_audio_clip = AudioClips.objects.filter(
                        audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        generic_status__generic_status_name='ok',
                        is_banned=False,
                    ).order_by('when_created', 'id')[:1]

                    earliest_audio_clip = earliest_audio_clip[0]

                    cursor_token = encode_cursor_token({
                        'when_created': earliest_audio_clip.when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                        'id': earliest_audio_clip.id,
                    })

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': cursor_token,
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #next_token, back_token, data
                    response_data = get_response_data(request)

                    self.assertEqual(len(response_data['data']), 0)
                    self.assertEqual(response_data['next_token'], response_data['back_token'])
                    self.assertEqual(response_data['next_token'], cursor_token)

                    #==========
                    #API back+token
                    #will always have rows
                    #==========

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

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    #check rows
                    self._general_row_check(response_data, current_kwargs)

                    #check tokens
                    self._general_cursor_token_check(response_data, audio_clip_role_name)

                    self.assertEqual(len(response_data['data']), settings.EVENT_QUANTITY_PER_PAGE)

                    #==========
                    #API back+token
                    #can guarantee to have rows but not row count
                    #==========

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

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    self.assertGreater(len(response_data['data']), 0)

                except Exception as e:

                    #show useful info

                    print(current_kwargs)
                    print(f'is_excluded_audio_clip_tone: {is_excluded_audio_clip_tone}')

                    if 'cursor_token' in current_kwargs:

                        print(f'cursor_token: {decode_cursor_token(current_kwargs['cursor_token'])}')

                    #check if can retry

                    if retries_left > 0:

                        #can retry

                        print('Retrying test to ensure failure is not related to db caching.')

                        retries_left -= 1

                        continue

                    #cannot retry
                    raise e

                #success, break while-loop
                break


    def test_browse_events__own_page(self, minimum_time_elapsed_ms=300, skip_to_loop=None):

        stopwatch = Stopwatch()

        #create all possible test cases

        #{'api_kwargs': {}, 'test_values': {}}
        test_cases = []

        #need to test all users, since some users can have 0 rows
        for login_user in self.main_users:

            for audio_clip_role_name in ['originator', 'responder']:

                expected_event_generic_status_names = []

                if audio_clip_role_name == 'originator':

                    expected_event_generic_status_names = ['incomplete', 'completed']

                else:

                    expected_event_generic_status_names = ['completed', 'deleted']

                #add "no audio_clip_tone selected"
                current_kwargs = {
                    'username': login_user.username,
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': audio_clip_role_name,
                    'next_or_back': 'next',
                }

                test_cases.append({
                    'api_kwargs': current_kwargs,
                    'test_values': {
                        'is_excluded_audio_clip_tone': False,
                        'login_user': login_user,
                        'target_user': login_user,
                        'expected_event_generic_status_names': expected_event_generic_status_names,
                    }
                })

                #others
                for audio_clip_tone_index, audio_clip_tone in enumerate(self.realistic_bulk_data_class.audio_clip_tones):

                    is_excluded_audio_clip_tone = audio_clip_tone_index in self.realistic_bulk_data_class.excluded_audio_clip_tones_indexes

                    current_kwargs = {
                        'username': login_user.username,
                        'latest_or_best': 'latest',
                        'timeframe': 'all',
                        'audio_clip_role_name': audio_clip_role_name,
                        'next_or_back': 'next',
                        'audio_clip_tone_id': audio_clip_tone.id,
                    }

                    test_cases.append({
                        'api_kwargs': current_kwargs,
                        'test_values': {
                            'is_excluded_audio_clip_tone': is_excluded_audio_clip_tone,
                            'login_user': login_user,
                            'target_user': login_user,
                            'expected_event_generic_status_names': expected_event_generic_status_names,
                        }
                    })

        #start test

        #use this to skip directly to problematic test
        skip_to_index = 0

        for test_index, test_case in enumerate(test_cases):

            if test_index < skip_to_index:

                print(f'Skipping test #{test_index} towards #{skip_to_index}.')
                continue

            #unpack test_case

            #some queries on first run will cause delay due to lack of caching at db
            #if exceeding minimum_time_elapsed_ms, retry once

            login_user = test_case['test_values']['login_user']
            target_user = test_case['test_values']['target_user']
            audio_clip_role_name = test_case['api_kwargs']['audio_clip_role_name']
            is_excluded_audio_clip_tone = test_case['test_values']['is_excluded_audio_clip_tone']
            expected_event_generic_status_names = test_case['test_values']['expected_event_generic_status_names']

            self.login(login_user)

            retries_left = 1

            while retries_left >= 0:

                #must .copy() so retrying will not reuse cursor and exceed rows available
                current_kwargs = test_case['api_kwargs'].copy()

                try:

                    loop_title = 'loop #' + str(test_index)

                    print(loop_title)

                    if skip_to_loop is not None and test_index != skip_to_loop:

                        break

                    #========================================
                    #part 1: from latest audio_clip
                    #========================================

                    #==========
                    #API next
                    #==========

                    #only for excluded audio_clip_tone, just to check that 0 row performance is ok
                    #event.generic_status is more varied now too, so starting cursor is essential for normal tests

                    if is_excluded_audio_clip_tone is True:

                        stopwatch.start()

                        request = self.client.get(
                            reverse(
                                'browse_events_api',
                                kwargs=current_kwargs
                            )
                        )

                        stopwatch.stop()

                        if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                            raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                        else:

                            print(f'Good: {stopwatch.diff_milliseconds()}')

                        #check

                        self.assertEqual(request.status_code, 200)

                        #response_data: next_token, back_token, data
                        #response_data['data']: [{event:event,originator:[],responder:[]}]
                        response_data = get_response_data(request)

                        self.assertEqual(len(response_data['data']), 0)

                        #skip to next test case
                        break

                    #==========
                    #API next+token
                    #==========

                    #immediately create cursor here
                    #guarantees at least 1 event with desired generic_status

                    latest_audio_clip = AudioClips.objects.filter(
                        user=target_user,
                        audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        generic_status__generic_status_name='ok',
                        event__generic_status__generic_status_name__in=expected_event_generic_status_names,
                        is_banned=False,
                    ).order_by('-when_created', '-id').first()

                    cursor_token = encode_cursor_token({
                        'when_created': latest_audio_clip.when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                        'id': latest_audio_clip.id,
                    })

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': cursor_token,
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    self.assertGreater(len(response_data['data']), 0)

                    #check rows
                    self._general_row_check(response_data, current_kwargs, is_event_always_completed=False)

                    #keep this for next->back validation later
                    first_response_data = response_data['data'].copy()

                    #check tokens
                    self._general_cursor_token_check(response_data, audio_clip_role_name)

                    #==========
                    #API next+token
                    #==========

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': response_data['next_token'],
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    self.assertGreater(len(response_data['data']), 0)

                    #check rows
                    self._general_row_check(response_data, current_kwargs, is_event_always_completed=False)

                    #check tokens
                    self._general_cursor_token_check(response_data, audio_clip_role_name)

                    #==========
                    #API back+token
                    #==========

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

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    #check rows
                    self._general_row_check(response_data, current_kwargs, is_event_always_completed=False)

                    #check tokens
                    self._general_cursor_token_check(response_data, audio_clip_role_name)

                    #ensure everything is the same as first response

                    self.assertEqual(len(response_data['data']), len(first_response_data))

                    for index in range(len(response_data['data'])):

                        if len(response_data['data'][index]['originator']) > 0:

                            self.assertEqual(
                                response_data['data'][index]['originator'][0]['id'],
                                first_response_data[index]['originator'][0]['id'],
                            )

                        if len(response_data['data'][index]['responder']) > 0:

                            self.assertEqual(
                                response_data['data'][index]['responder'][0]['id'],
                                first_response_data[index]['responder'][0]['id'],
                            )

                    #==========
                    #API another back+token
                    #==========

                    #our original testing cursor involves only x event__generic_status
                    #but main query allows for multiple event__generic_status
                    #doing this second back+token cannot guarantee that rows are 0 or > 0
                    #no need to do

                    #========================================
                    #part 2: from earliest audio_clip
                    #========================================

                    #==========
                    #API next with last row in db
                    #expect 0 rows
                    #==========

                    #construct our own cursor from earliest eligible audio_clip

                    earliest_audio_clip = AudioClips.objects.filter(
                        user=target_user,
                        audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        generic_status__generic_status_name='ok',
                        event__generic_status__generic_status_name__in=expected_event_generic_status_names,
                        is_banned=False,
                    ).order_by('when_created', 'id')[:1]

                    earliest_audio_clip = earliest_audio_clip[0]

                    cursor_token = encode_cursor_token({
                        'when_created': earliest_audio_clip.when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                        'id': earliest_audio_clip.id,
                    })

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': cursor_token,
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #next_token, back_token, data
                    response_data = get_response_data(request)

                    self.assertEqual(len(response_data['data']), 0)

                    #==========
                    #API back+token
                    #will always have rows
                    #==========

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

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    self.assertGreater(len(response_data['data']), 0)

                    #check rows
                    self._general_row_check(response_data, current_kwargs, is_event_always_completed=False)

                    #check tokens
                    self._general_cursor_token_check(response_data, audio_clip_role_name)

                    #==========
                    #API next+token
                    #don't test for row count because it cannot be guaranteed
                    #==========

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': response_data['next_token'],
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                except Exception as e:

                    #show useful info

                    print(current_kwargs)
                    print(f'is_excluded_audio_clip_tone: {is_excluded_audio_clip_tone}')

                    if 'cursor_token' in current_kwargs:

                        print(f'cursor_token: {decode_cursor_token(current_kwargs['cursor_token'])}')

                    #check if can retry

                    if retries_left > 0:

                        #can retry

                        print('Retrying test to ensure failure is not related to db caching.')

                        retries_left -= 1

                        continue

                    #cannot retry
                    raise e

                #success, break while-loop
                break


    def test_browse_events__other_user_page(self, minimum_time_elapsed_ms=300, skip_to_loop=None):

        stopwatch = Stopwatch()

        #create all possible test cases

        #{'api_kwargs': {}, 'test_values': {}}
        test_cases = []

        #need to test all users, since some users can have 0 rows
        for login_user in self.main_users:

            for target_user in self.main_users:

                if login_user.id == target_user.id:

                    #don't open own page
                    continue

                for audio_clip_role_name in ['originator', 'responder']:

                    expected_event_generic_status_names = []

                    if audio_clip_role_name == 'originator':

                        expected_event_generic_status_names = ['incomplete', 'completed']

                    else:

                        expected_event_generic_status_names = ['completed', 'deleted']

                    #add "no audio_clip_tone selected"
                    current_kwargs = {
                        'username': target_user.username,
                        'latest_or_best': 'latest',
                        'timeframe': 'all',
                        'audio_clip_role_name': audio_clip_role_name,
                        'next_or_back': 'next',
                    }

                    test_cases.append({
                        'api_kwargs': current_kwargs,
                        'test_values': {
                            'is_excluded_audio_clip_tone': False,
                            'login_user': login_user,
                            'target_user': target_user,
                            'expected_event_generic_status_names': expected_event_generic_status_names,
                        }
                    })

                    #others
                    for audio_clip_tone_index, audio_clip_tone in enumerate(self.realistic_bulk_data_class.audio_clip_tones):

                        is_excluded_audio_clip_tone = audio_clip_tone_index in self.realistic_bulk_data_class.excluded_audio_clip_tones_indexes

                        current_kwargs = {
                            'username': target_user.username,
                            'latest_or_best': 'latest',
                            'timeframe': 'all',
                            'audio_clip_role_name': audio_clip_role_name,
                            'next_or_back': 'next',
                            'audio_clip_tone_id': audio_clip_tone.id,
                        }

                        test_cases.append({
                            'api_kwargs': current_kwargs,
                            'test_values': {
                                'is_excluded_audio_clip_tone': is_excluded_audio_clip_tone,
                                'login_user': login_user,
                                'target_user': login_user,
                                'expected_event_generic_status_names': expected_event_generic_status_names,
                            }
                        })

        #start test

        #use this to skip directly to problematic test
        skip_to_index = 0

        for test_index, test_case in enumerate(test_cases):

            if test_index < skip_to_index:

                print(f'Skipping test #{test_index} towards #{skip_to_index}.')
                continue

            #unpack test_case

            #some queries on first run will cause delay due to lack of caching at db
            #if exceeding minimum_time_elapsed_ms, retry once

            login_user = test_case['test_values']['login_user']
            target_user = test_case['test_values']['target_user']
            audio_clip_role_name = test_case['api_kwargs']['audio_clip_role_name']
            is_excluded_audio_clip_tone = test_case['test_values']['is_excluded_audio_clip_tone']
            expected_event_generic_status_names = test_case['test_values']['expected_event_generic_status_names']

            self.login(login_user)

            retries_left = 1

            while retries_left >= 0:

                #must .copy() so retrying will not reuse cursor and exceed rows available
                current_kwargs = test_case['api_kwargs'].copy()

                try:

                    loop_title = 'loop #' + str(test_index)

                    print(loop_title)

                    if skip_to_loop is not None and test_index != skip_to_loop:

                        break

                    #========================================
                    #part 1: from latest audio_clip
                    #========================================

                    #==========
                    #API next
                    #==========

                    #only for excluded audio_clip_tone, just to check that 0 row performance is ok
                    #event.generic_status is more varied now too, so starting cursor is essential for normal tests

                    if is_excluded_audio_clip_tone is True:

                        stopwatch.start()

                        request = self.client.get(
                            reverse(
                                'browse_events_api',
                                kwargs=current_kwargs
                            )
                        )

                        stopwatch.stop()

                        if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                            raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                        else:

                            print(f'Good: {stopwatch.diff_milliseconds()}')

                        #check

                        self.assertEqual(request.status_code, 200)

                        #response_data: next_token, back_token, data
                        #response_data['data']: [{event:event,originator:[],responder:[]}]
                        response_data = get_response_data(request)

                        self.assertEqual(len(response_data['data']), 0)

                        #skip to next test case
                        break

                    #==========
                    #API next+token
                    #==========

                    #immediately create cursor here
                    #guarantees at least 1 event with desired generic_status

                    latest_audio_clip = AudioClips.objects.filter(
                        user=target_user,
                        audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        generic_status__generic_status_name='ok',
                        event__generic_status__generic_status_name__in=expected_event_generic_status_names,
                        is_banned=False,
                    ).order_by('-when_created', '-id').first()

                    cursor_token = encode_cursor_token({
                        'when_created': latest_audio_clip.when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                        'id': latest_audio_clip.id,
                    })

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': cursor_token,
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    self.assertGreater(len(response_data['data']), 0)

                    #check rows
                    self._general_row_check(response_data, current_kwargs, is_event_always_completed=False)

                    #check tokens
                    self._general_cursor_token_check(response_data, audio_clip_role_name)

                    #keep this for next->back validation later
                    first_response_data = response_data['data'].copy()

                    #==========
                    #API next+token
                    #==========

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

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    self.assertGreater(len(response_data['data']), 0)

                    #check rows
                    self._general_row_check(response_data, current_kwargs, is_event_always_completed=False)

                    #check tokens
                    self._general_cursor_token_check(response_data, audio_clip_role_name)

                    #==========
                    #API back+token
                    #==========

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

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    #check rows
                    self._general_row_check(response_data, current_kwargs, is_event_always_completed=False)

                    #check tokens
                    self._general_cursor_token_check(response_data, audio_clip_role_name)

                    #ensure everything is the same as first response

                    self.assertEqual(len(response_data['data']), len(first_response_data))

                    for index in range(len(response_data['data'])):

                        if len(response_data['data'][index]['originator']) > 0:

                            self.assertEqual(
                                response_data['data'][index]['originator'][0]['id'],
                                first_response_data[index]['originator'][0]['id'],
                            )

                        if len(response_data['data'][index]['responder']) > 0:

                            self.assertEqual(
                                response_data['data'][index]['responder'][0]['id'],
                                first_response_data[index]['responder'][0]['id'],
                            )

                    #==========
                    #API another back+token
                    #==========

                    #no need to do, because we only fetch x event__generic_status but main query allows multiple event__generic_status

                    #========================================
                    #part 2: from earliest audio_clip
                    #========================================

                    #==========
                    #API next
                    #don't test for row count because it cannot be guaranteed
                    #==========

                    #construct our own cursor from earliest eligible audio_clip

                    earliest_audio_clip = AudioClips.objects.filter(
                        user=target_user,
                        audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        generic_status__generic_status_name='ok',
                        event__generic_status__generic_status_name__in=expected_event_generic_status_names,
                        is_banned=False,
                    ).order_by('-when_created', '-id').last()

                    cursor_token = encode_cursor_token({
                        'when_created': earliest_audio_clip.when_created.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                        'id': earliest_audio_clip.id,
                    })

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': cursor_token,
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #next_token, back_token, data
                    response_data = get_response_data(request)

                    #==========
                    #API back+token
                    #will always have rows
                    #==========

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

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    self.assertGreater(len(response_data['data']), 0)

                    #check rows
                    self._general_row_check(response_data, current_kwargs, is_event_always_completed=False)

                    #check tokens
                    self._general_cursor_token_check(response_data, audio_clip_role_name)

                    #==========
                    #API next+token
                    #don't test for row count because it cannot be guaranteed
                    #==========

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': response_data['next_token'],
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                except Exception as e:

                    #show useful info

                    print(current_kwargs)
                    print(f'is_excluded_audio_clip_tone: {is_excluded_audio_clip_tone}')

                    if 'cursor_token' in current_kwargs:

                        print(f'cursor_token: {decode_cursor_token(current_kwargs['cursor_token'])}')

                    #check if can retry

                    if retries_left > 0:

                        #can retry

                        print('Retrying test to ensure failure is not related to db caching.')

                        retries_left -= 1

                        continue

                    #cannot retry
                    raise e

                #success, break while-loop
                break


    def test_browse_events__own_like_dislike_page(self, minimum_time_elapsed_ms=300, skip_to_loop=None):

        #pre-determine audio_clip_tones
        #since excluded tones are specified in earliest/middle/latest manner, #and will never use first and last,
        #can just make sure we don't -1 for earliest, and +1 for latest

        excluded_audio_clip_tone_ids = []
        expected_audio_clip_tone_ids = [None]

        realistic_bulk_data_class = RealisticBulkData()

        #get first tone to prevent repeated if-statements

        excluded_audio_clip_tone_ids.append(
            realistic_bulk_data_class.audio_clip_tones[
                realistic_bulk_data_class.excluded_audio_clip_tones_indexes[0]
            ].id
        )

        expected_audio_clip_tone_ids.append(
            realistic_bulk_data_class.audio_clip_tones[
                realistic_bulk_data_class.excluded_audio_clip_tones_indexes[0] + 1
            ].id
        )

        #add excluded audio_clip_tones
        for index in range(1, len(realistic_bulk_data_class.excluded_audio_clip_tones_indexes)):

            excluded_index = realistic_bulk_data_class.excluded_audio_clip_tones_indexes[index]

            excluded_audio_clip_tone_ids.append(
                realistic_bulk_data_class.audio_clip_tones[excluded_index].id
            )

            expected_audio_clip_tone_ids.append(
                realistic_bulk_data_class.audio_clip_tones[excluded_index - 1].id
            )

        stopwatch = Stopwatch()

        #create all possible test cases

        #{'api_kwargs': {}, 'test_values': {}}
        test_cases = []

        audio_clip_tone_ids = expected_audio_clip_tone_ids + excluded_audio_clip_tone_ids

        for login_user in self.realistic_bulk_data_class.main_users:

            for audio_clip_role_name in ['originator', 'responder']:

                expected_event_generic_status_names = []

                if audio_clip_role_name == 'originator':

                    expected_event_generic_status_names = ['incomplete', 'completed']

                else:

                    expected_event_generic_status_names = ['completed', 'deleted']

                for expected_event_generic_status_name in expected_event_generic_status_names:

                    for likes_or_dislikes in ['likes', 'dislikes']:

                        for audio_clip_tone_id_index, audio_clip_tone_id in enumerate(audio_clip_tone_ids):

                            is_excluded_audio_clip_tone = False

                            if (audio_clip_tone_id_index + 1) > len(expected_audio_clip_tone_ids):

                                is_excluded_audio_clip_tone = True

                            current_kwargs = {
                                'username': login_user.username,
                                'latest_or_best': 'latest',
                                'timeframe': 'all',
                                'audio_clip_role_name': audio_clip_role_name,
                                'next_or_back': 'next',
                                'likes_or_dislikes': likes_or_dislikes,
                            }

                            if audio_clip_tone_id is not None:

                                current_kwargs.update({'audio_clip_tone_id': audio_clip_tone_id})

                            test_cases.append({
                                'api_kwargs': current_kwargs,
                                'test_values': {
                                    'is_excluded_audio_clip_tone': is_excluded_audio_clip_tone,
                                    'login_user': login_user,
                                    'target_user': login_user,
                                    'expected_event_generic_status_name': expected_event_generic_status_name,
                                }
                            })

        #start test

        for test_index, test_case in enumerate(test_cases):

            #unpack test_case
            #lazy solution for implementing this after main code has been written

            current_kwargs = test_case['api_kwargs']
            login_user = test_case['test_values']['login_user']
            target_user = test_case['test_values']['target_user']
            audio_clip_role_name = test_case['api_kwargs']['audio_clip_role_name']
            is_excluded_audio_clip_tone = test_case['test_values']['is_excluded_audio_clip_tone']
            expected_event_generic_status_name = test_case['test_values']['expected_event_generic_status_name']

            self.login(login_user)

            #some queries on first run will cause delay due to lack of caching at db
            #if exceeding minimum_time_elapsed_ms, retry once

            retries_left = 1

            while retries_left >= 0:

                try:

                    loop_title = 'loop #' + str(test_index)

                    print(loop_title)

                    if skip_to_loop is not None and test_index != skip_to_loop:

                        break

                    #========================================
                    #part 1: from latest audio_clip
                    #========================================

                    #==========
                    #API next
                    #==========

                    #only for excluded audio_clip_tone, just to check that 0 row performance is ok
                    #event.generic_status is more varied now too, so starting cursor is essential for normal tests

                    if is_excluded_audio_clip_tone is True:

                        stopwatch.start()

                        request = self.client.get(
                            reverse(
                                'browse_events_api',
                                kwargs=current_kwargs
                            )
                        )

                        stopwatch.stop()

                        if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                            raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                        else:

                            print(f'Good: {stopwatch.diff_milliseconds()}')

                        #check

                        self.assertEqual(request.status_code, 200)

                        #response_data: next_token, back_token, data
                        #response_data['data']: [{event:event,originator:[],responder:[]}]
                        response_data = get_response_data(request)

                        self.assertEqual(len(response_data['data']), 0)

                        #skip to next test case
                        break

                    #==========
                    #API next+token
                    #==========

                    #immediately create cursor here
                    #guarantees at least 1 event with desired generic_status

                    latest_audio_clip_like_dislike = AudioClipLikesDislikes.objects.filter(
                        user=target_user,
                        is_liked=(likes_or_dislikes == 'likes'),
                        audio_clip__audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        audio_clip__generic_status__generic_status_name='ok',
                        audio_clip__event__generic_status__generic_status_name=expected_event_generic_status_name,
                        audio_clip__is_banned=False,
                    ).order_by('-last_modified', '-id').first()

                    cursor_token = encode_cursor_token({
                        'last_modified': latest_audio_clip_like_dislike.last_modified.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                        'id': latest_audio_clip_like_dislike.id,
                    })

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': cursor_token,
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    self.assertGreater(len(response_data['data']), 0)

                    #check rows
                    self._general_row_check(response_data, current_kwargs, is_event_always_completed=False)

                    #check tokens
                    self._like_dislike_cursor_token_check(response_data, audio_clip_role_name, target_user)

                    #keep this for next->back validation later
                    first_response_data = response_data['data'].copy()

                    #==========
                    #API next+token
                    #==========

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': response_data['next_token'],
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    self.assertGreater(len(response_data['data']), 0)

                    #check rows
                    self._general_row_check(response_data, current_kwargs, is_event_always_completed=False)

                    #check tokens
                    self._like_dislike_cursor_token_check(response_data, audio_clip_role_name, target_user)

                    #==========
                    #API back+token
                    #==========

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

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    #check rows
                    self._general_row_check(response_data, current_kwargs, is_event_always_completed=False)

                    #check tokens
                    self._like_dislike_cursor_token_check(response_data, audio_clip_role_name, target_user)

                    #ensure everything is the same as first response

                    self.assertEqual(len(response_data['data']), len(first_response_data))

                    for index in range(len(response_data['data'])):

                        if response_data['data'][index]['originator']:

                            self.assertEqual(
                                response_data['data'][index]['originator'][0]['id'],
                                first_response_data[index]['originator'][0]['id'],
                            )

                        if response_data['data'][index]['responder']:

                            self.assertEqual(
                                response_data['data'][index]['responder'][0]['id'],
                                first_response_data[index]['responder'][0]['id'],
                            )

                    #==========
                    #API another back+token
                    #==========

                    #no need to do, because we only fetch x event__generic_status but main query allows multiple event__generic_status

                    #========================================
                    #part 2: from earliest audio_clip
                    #========================================

                    #==========
                    #API next
                    #don't test for row count because it cannot be guaranteed
                    #==========

                    #construct our own cursor from earliest eligible audio_clip

                    earliest_audio_clip_like_dislike = AudioClipLikesDislikes.objects.filter(
                        user=target_user,
                        is_liked=(likes_or_dislikes == 'likes'),
                        audio_clip__audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        audio_clip__generic_status__generic_status_name='ok',
                        audio_clip__event__generic_status__generic_status_name=expected_event_generic_status_name,
                        audio_clip__is_banned=False,
                    ).order_by('-last_modified', '-id').last()

                    cursor_token = encode_cursor_token({
                        'last_modified': earliest_audio_clip_like_dislike.last_modified.strftime('%Y-%m-%d %H:%M:%S.%f %z'),
                        'id': earliest_audio_clip_like_dislike.id,
                    })

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': cursor_token,
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #next_token, back_token, data
                    response_data = get_response_data(request)

                    #==========
                    #API back+token
                    #guaranteed to have rows
                    #==========

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

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                    self.assertGreater(len(response_data['data']), 0)

                    #check rows
                    self._general_row_check(response_data, current_kwargs, is_event_always_completed=False)

                    #check tokens
                    self._like_dislike_cursor_token_check(response_data, audio_clip_role_name, target_user)

                    #==========
                    #API next+token
                    #don't count rows because it cannot be guaranteed
                    #==========

                    current_kwargs.update({
                        'next_or_back': 'next',
                        'cursor_token': response_data['next_token'],
                    })

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    if stopwatch.diff_milliseconds() >= minimum_time_elapsed_ms:

                        raise ValueError(f'Query time exceeded: {stopwatch.diff_milliseconds()}')

                    else:

                        print(f'Good: {stopwatch.diff_milliseconds()}')

                    #check

                    self.assertEqual(request.status_code, 200)

                    #response_data: next_token, back_token, data
                    #response_data['data']: [{event:event,originator:[],responder:[]}]
                    response_data = get_response_data(request)

                except Exception as e:

                    #show useful info

                    print(current_kwargs)
                    print(f'is_excluded_audio_clip_tone: {is_excluded_audio_clip_tone}')
                    print(f'expected_event_generic_status_name: {expected_event_generic_status_name}')

                    if 'cursor_token' in current_kwargs:

                        print(f'cursor_token: {decode_cursor_token(current_kwargs['cursor_token'])}')

                    #check if can retry

                    if retries_left > 0:

                        #can retry

                        print('Retrying test to ensure failure is not related to db caching.')

                        retries_left -= 1

                        continue

                    #cannot retry
                    raise e

                #success, break while-loop
                break












#how to test:
    #test each test_() individually, as running all tests concurrently will have worse performance
#only test for basic correctness and db test data setup
#leave API correctness at test_apis
@override_settings(
    DEBUG=True,
)
class ListEventReplyChoices_TestCase(TestCase):

    #{test_function_name: anything}
    metrics = {}


    @classmethod
    def setUpTestData(cls):

        cls.realistic_bulk_data_class = RealisticBulkData()

        result = cls.realistic_bulk_data_class.get_main_users_relative_to_entire_db()
        cls.main_users = result['main_users']
        cls.main_user_sets = result['main_user_sets']


    #WINNER
    #always no tone specified
    #has ORDER BY events.when_created
    def _query_0(self, current_user_id:int, when_created:datetime):

        stopwatch = Stopwatch()

        stopwatch.start()

        query = '''
            WITH
                excluded_events_1 AS (
                    SELECT id FROM events
                    WHERE created_by_id = %s
                ),
                excluded_events_2 AS (
                    SELECT event_id AS id FROM user_events
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
                narrowed_events AS (
                    SELECT events.id FROM events
                    WHERE generic_status_id = (SELECT id FROM generic_statuses WHERE generic_status_name = %s)
                    AND when_created >= %s
                ),
                target_events AS (
                    SELECT events.* FROM events
                    INNER JOIN narrowed_events ON narrowed_events.id = events.id
                    LEFT JOIN event_reply_queues ON event_reply_queues.event_id = events.id
                    LEFT JOIN excluded_events_1 ON excluded_events_1.id = events.id
                    LEFT JOIN excluded_events_2 ON excluded_events_2.id = events.id
                    LEFT JOIN excluded_users_1 ON events.created_by_id = excluded_users_1.id
                    LEFT JOIN excluded_users_2 ON events.created_by_id = excluded_users_2.id
                    WHERE event_reply_queues.event_id IS NULL
                    AND excluded_events_1.id IS NULL
                    AND excluded_events_2.id IS NULL
                    AND excluded_users_1.id IS NULL
                    AND excluded_users_2.id IS NULL
                    LIMIT 1
                )
                SELECT
                    audio_clips.*,
                    audio_clip_likes_dislikes.is_liked AS is_liked_by_user,
                    audio_clip_metrics.like_count AS like_count,
                    audio_clip_metrics.dislike_count AS dislike_count
                FROM audio_clips
                INNER JOIN target_events ON audio_clips.event_id = target_events.id
                LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id
                    AND audio_clip_likes_dislikes.user_id = %s
                LEFT JOIN audio_clip_metrics ON audio_clips.id = audio_clip_metrics.audio_clip_id
                WHERE audio_clips.is_banned IS FALSE
                AND audio_clips.audio_clip_role_id = (
                    SELECT id FROM audio_clip_roles
                    WHERE audio_clip_role_name = %s
                )
                AND audio_clips.generic_status_id = (
                    SELECT id FROM generic_statuses
                    WHERE generic_status_name = %s
                )
                ORDER BY target_events.when_created ASC
                LIMIT 1
        '''

        params = [
            current_user_id,
            current_user_id,
            current_user_id,
            current_user_id,
            'incomplete',
            when_created,
            current_user_id,
            'originator',
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
            query,
            params
        )

        #immediately execute, else 0 at stopwatch
        len(audio_clips)

        stopwatch.stop()

        return {
            'query_result': audio_clips,
            'time_elapsed_ms': stopwatch.diff_milliseconds(),
            'raw_query': connection.cursor().mogrify(query, params),
        }


    #always has tone specified
    def _query_1(self, current_user_id:int, audio_clip_tone_id:int, when_created:datetime):

        stopwatch = Stopwatch()

        stopwatch.start()

        query = '''
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
                ),
                narrowed_down_events AS (
                    SELECT events.id FROM events
                    WHERE generic_status_id = (SELECT id FROM generic_statuses WHERE generic_status_name = %s)
                    AND when_created >= %s
                    ORDER BY when_created
                ),
                specific_tone_events AS (
                    SELECT events.id FROM events
                    INNER JOIN narrowed_down_events ON events.id = narrowed_down_events.id
                    INNER JOIN audio_clips ON events.id = audio_clips.event_id
                    WHERE audio_clips.audio_clip_tone_id = %s
                    AND audio_clips.audio_clip_role_id = (SELECT id FROM audio_clip_roles WHERE audio_clip_role_name=%s)
                    AND audio_clips.generic_status_id = (SELECT id FROM generic_statuses WHERE generic_status_name=%s)
                ),
                target_events AS (
                    SELECT events.* FROM events
                    INNER JOIN specific_tone_events ON specific_tone_events.id = events.id
                    LEFT JOIN event_reply_queues ON event_reply_queues.event_id = events.id
                    LEFT JOIN excluded_events_1 ON excluded_events_1.event_id = events.id
                    LEFT JOIN excluded_events_2 ON excluded_events_2.event_id = events.id
                    LEFT JOIN excluded_users_1 ON events.created_by_id = excluded_users_1.id
                    LEFT JOIN excluded_users_2 ON events.created_by_id = excluded_users_2.id
                    WHERE event_reply_queues.event_id IS NULL
                    AND excluded_events_1.event_id IS NULL
                    AND excluded_events_2.event_id IS NULL
                    AND excluded_users_1.id IS NULL
                    AND excluded_users_2.id IS NULL
                    LIMIT 1
                )
                SELECT
                    audio_clips.*,
                    audio_clip_likes_dislikes.is_liked AS is_liked_by_user,
                    audio_clip_metrics.like_count AS like_count,
                    audio_clip_metrics.dislike_count AS dislike_count
                FROM audio_clips
                INNER JOIN target_events ON audio_clips.event_id = target_events.id
                LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id
                    AND audio_clip_likes_dislikes.user_id = 1
                LEFT JOIN audio_clip_metrics ON audio_clips.id = audio_clip_metrics.audio_clip_id
                WHERE audio_clips.is_banned IS FALSE
                AND audio_clips.audio_clip_role_id = (
                    SELECT id FROM audio_clip_roles
                    WHERE audio_clip_role_name = %s
                )
                AND audio_clips.generic_status_id = (
                    SELECT id FROM generic_statuses
                    WHERE generic_status_name = %s
                )
                LIMIT 1
        '''
        
        params = [
            current_user_id,
            current_user_id,
            current_user_id,
            current_user_id,
            'incomplete',
            when_created,
            audio_clip_tone_id,
            'originator',
            'ok',
            'originator',
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
            query,
            params
        )

        #immediately execute, else 0 at stopwatch
        len(audio_clips)

        stopwatch.stop()

        return {
            'query_result': audio_clips,
            'time_elapsed_ms': stopwatch.diff_milliseconds(),
            'raw_query': connection.cursor().mogrify(query, params),
        }


    #always no tone specified
    #has no ORDER_BY events.when_created
    #cons:
        #cannot guarantee that every event gets an equal chance
    def _query_2(self, current_user_id:int, when_created:datetime):

        stopwatch = Stopwatch()

        stopwatch.start()

        query = '''
            WITH
                excluded_events_1 AS (
                    SELECT id FROM events
                    WHERE created_by_id = %s
                ),
                excluded_events_2 AS (
                    SELECT event_id AS id FROM user_events
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
                narrowed_events AS (
                    SELECT events.id FROM events
                    WHERE generic_status_id = (SELECT id FROM generic_statuses WHERE generic_status_name = %s)
                    AND when_created >= %s
                ),
                target_events AS (
                    SELECT events.* FROM events
                    INNER JOIN narrowed_events ON narrowed_events.id = events.id
                    LEFT JOIN event_reply_queues ON event_reply_queues.event_id = events.id
                    LEFT JOIN excluded_events_1 ON excluded_events_1.id = events.id
                    LEFT JOIN excluded_events_2 ON excluded_events_2.id = events.id
                    LEFT JOIN excluded_users_1 ON events.created_by_id = excluded_users_1.id
                    LEFT JOIN excluded_users_2 ON events.created_by_id = excluded_users_2.id
                    WHERE event_reply_queues.event_id IS NULL
                    AND excluded_events_1.id IS NULL
                    AND excluded_events_2.id IS NULL
                    AND excluded_users_1.id IS NULL
                    AND excluded_users_2.id IS NULL
                    LIMIT 1
                )
                SELECT
                    audio_clips.*,
                    audio_clip_likes_dislikes.is_liked AS is_liked_by_user,
                    audio_clip_metrics.like_count AS like_count,
                    audio_clip_metrics.dislike_count AS dislike_count
                FROM audio_clips
                INNER JOIN target_events ON audio_clips.event_id = target_events.id
                LEFT JOIN audio_clip_likes_dislikes ON audio_clips.id = audio_clip_likes_dislikes.audio_clip_id
                    AND audio_clip_likes_dislikes.user_id = %s
                LEFT JOIN audio_clip_metrics ON audio_clips.id = audio_clip_metrics.audio_clip_id
                WHERE audio_clips.is_banned IS FALSE
                AND audio_clips.audio_clip_role_id = (
                    SELECT id FROM audio_clip_roles
                    WHERE audio_clip_role_name = %s
                )
                AND audio_clips.generic_status_id = (
                    SELECT id FROM generic_statuses
                    WHERE generic_status_name = %s
                )
                LIMIT 1
        '''

        params = [
            current_user_id,
            current_user_id,
            current_user_id,
            current_user_id,
            'incomplete',
            when_created,
            current_user_id,
            'originator',
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
            query,
            params
        )

        #immediately execute, else 0 at stopwatch
        len(audio_clips)

        stopwatch.stop()

        return {
            'query_result': audio_clips,
            'time_elapsed_ms': stopwatch.diff_milliseconds(),
            'raw_query': connection.cursor().mogrify(query, params),
        }


    def test_list_event_reply_choices(self, has_tone=False, minimum_time_elapsed_ms=180, show_test_failed_query=True, show_test_passed_query=False):

        stopwatch = Stopwatch()

        #do this for no tone so loop below can stay the same
        audio_clip_tone_ids = {
            'no_audio_clip_tone': [None],
        }

        if has_tone is True:

            audio_clip_tone_ids = {
                'excluded': [],
                'expected': [],
            }

            #add excluded audio_clip_tones
            for audio_clip_tone_index in self.realistic_bulk_data_class.excluded_audio_clip_tones_indexes:

                audio_clip_tone_ids['excluded'].append(
                    self.realistic_bulk_data_class.audio_clip_tones[audio_clip_tone_index].id
                )

                #since excluded tones are specified in earliest/middle/latest manner,
                #and will never use first and last,
                #can just -1 +1
                audio_clip_tone_ids['expected'].append(
                    self.realistic_bulk_data_class.audio_clip_tones[audio_clip_tone_index - 1].id
                )
                audio_clip_tone_ids['expected'].append(
                    self.realistic_bulk_data_class.audio_clip_tones[audio_clip_tone_index + 1].id
                )

        #since main users all have their own originator/responder processings,
        #we'll also need filler users to query this part properly

        test_pass_count = 0
        test_fail_count = 0

        for target_user in self.main_users:

            #check if has reply queue
            user_has_queue = EventReplyQueues.objects.filter(locked_for_user=target_user).exists()

            for audio_clip_tone_type in audio_clip_tone_ids:

                for audio_clip_tone_id in audio_clip_tone_ids[audio_clip_tone_type]:

                    minimum_datetimes = []

                    earliest_audio_clip = None
                    latest_audio_clip = None

                    if has_tone is True:

                        raise ValueError('Cannot use has_tone=True yet.')

                    else:

                        earliest_event = Events.objects.raw(
                            '''
                                WITH
                                excluded_events_1 AS (
                                    SELECT id FROM events
                                    WHERE created_by_id = %s
                                ),
                                excluded_events_2 AS (
                                    SELECT event_id AS id FROM user_events
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
                                SELECT events.* FROM events
                                LEFT JOIN event_reply_queues ON event_reply_queues.event_id = events.id
                                LEFT JOIN excluded_events_1 ON excluded_events_1.id = events.id
                                LEFT JOIN excluded_events_2 ON excluded_events_2.id = events.id
                                LEFT JOIN excluded_users_1 ON events.created_by_id = excluded_users_1.id
                                LEFT JOIN excluded_users_2 ON events.created_by_id = excluded_users_2.id
                                WHERE event_reply_queues.event_id IS NULL
                                AND excluded_events_1.id IS NULL
                                AND excluded_events_2.id IS NULL
                                AND excluded_users_1.id IS NULL
                                AND excluded_users_2.id IS NULL
                                AND events.generic_status_id = (
                                    SELECT id FROM generic_statuses WHERE generic_status_name = 'incomplete'
                                )
                                ORDER BY events.when_created ASC
                                LIMIT 1
                                ;
                            ''',
                            [
                                target_user.id,
                                target_user.id,
                                target_user.id,
                                target_user.id,
                            ]
                        )

                        latest_event = Events.objects.raw(
                            '''
                                WITH
                                excluded_events_1 AS (
                                    SELECT id FROM events
                                    WHERE created_by_id = %s
                                ),
                                excluded_events_2 AS (
                                    SELECT event_id AS id FROM user_events
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
                                SELECT events.* FROM events
                                LEFT JOIN event_reply_queues ON event_reply_queues.event_id = events.id
                                LEFT JOIN excluded_events_1 ON excluded_events_1.id = events.id
                                LEFT JOIN excluded_events_2 ON excluded_events_2.id = events.id
                                LEFT JOIN excluded_users_1 ON events.created_by_id = excluded_users_1.id
                                LEFT JOIN excluded_users_2 ON events.created_by_id = excluded_users_2.id
                                WHERE event_reply_queues.event_id IS NULL
                                AND excluded_events_1.id IS NULL
                                AND excluded_events_2.id IS NULL
                                AND excluded_users_1.id IS NULL
                                AND excluded_users_2.id IS NULL
                                AND events.generic_status_id = (
                                    SELECT id FROM generic_statuses WHERE generic_status_name = 'incomplete'
                                )
                                ORDER BY events.when_created DESC
                                LIMIT 1
                                ;
                            ''',
                            [
                                target_user.id,
                                target_user.id,
                                target_user.id,
                                target_user.id,
                            ]
                        )

                    #start

                    target_events = [earliest_event[0], latest_event[0]]

                    for target_event_index, target_event in enumerate(target_events):

                        minimum_datetime = target_event.when_created

                        result = None

                        #check if user has blocks/blocked/etc.
                        is_user_blocking = UserBlocks.objects.filter(
                            user=target_user,
                            blocked_user=earliest_event.created_by,
                        )
                        is_user_blocked = UserBlocks.objects.filter(
                            user=earliest_event.created_by,
                            blocked_user=target_user,
                        )

                        if has_tone is True:

                            result = self._query_1(
                                current_user_id=target_user.id,
                                audio_clip_tone_id=audio_clip_tone_id,
                                when_created=minimum_datetime,
                            )

                        else:

                            result = self._query_0(
                                current_user_id=target_user.id,
                                when_created=minimum_datetime,
                            )

                        #check

                        row_count = len(result['query_result'])

                        #only have row if nobody is blocking anyone
                        is_row_count_ok = (
                            ((is_user_blocking is True or is_user_blocked is True) and row_count == 0) or
                            ((is_user_blocking is False and is_user_blocked is False) and row_count == 1)
                        )

                        #specify minimum_time_elapsed_ms to hide/show benchmark that matters
                        if is_row_count_ok is True and result['time_elapsed_ms'] < minimum_time_elapsed_ms:
                        
                            print('\n')

                            if show_test_passed_query is True:
                            
                                print(result['raw_query'])

                            print('Good')
                            print({
                                'target_user_username': target_user.username,
                                'minimum_datetime': minimum_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                                'time_elapsed_ms': result['time_elapsed_ms'],
                            })
                            print('\n')

                            test_pass_count += 1

                            continue
                        
                        print('\n')

                        if show_test_failed_query is True:
                        
                            print(result['raw_query'])

                        #put {} if row count has issues, else None

                        row_count_issues = None

                        if is_row_count_ok is False:
                        
                            row_count_issues = {
                                'is_expecting_rows': True,
                                'query_row_count': len(result['query_result']),
                            }

                        print({
                            'row_count_issues': row_count_issues,
                            'target_user_username': target_user.username,
                            'earliest_or_latest_datetime': 'earliest' if target_event_index == 0 else 'latest',
                            'minimum_datetime': minimum_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                            'time_elapsed_ms': result['time_elapsed_ms'],
                        })
                        print('\n')

                        test_fail_count += 1

        print({
            'tests_passed': test_pass_count,
            'tests_failed': test_fail_count,
        })


    def test_experimental__has_tone(self, minimum_time_elapsed_ms=200, show_test_failed_query=False,):

        stopwatch = Stopwatch()

        excluded_audio_clip_tone_ids = []
        expected_audio_clip_tone_ids = []

        #add excluded audio_clip_tones
        for audio_clip_tone_index in self.realistic_bulk_data_class.excluded_audio_clip_tones_indexes:

            excluded_audio_clip_tone_ids.append(
                self.realistic_bulk_data_class.audio_clip_tones[audio_clip_tone_index].id
            )

            #since excluded tones are specified in earliest/middle/latest manner,
            #and will never use first and last,
            #can just -1 +1
            expected_audio_clip_tone_ids.append(
                self.realistic_bulk_data_class.audio_clip_tones[audio_clip_tone_index - 1].id
            )
            expected_audio_clip_tone_ids.append(
                self.realistic_bulk_data_class.audio_clip_tones[audio_clip_tone_index + 1].id
            )

        test_pass_count = 0
        test_fail_count = 0

        for target_user in self.main_users:

            #expect rows matching tone to exist
            for audio_clip_tone_id in expected_audio_clip_tone_ids:

                minimum_datetimes = []

                earliest_audio_clip = AudioClips.objects.filter(
                    generic_status__generic_status_name='ok',
                    audio_clip_role__audio_clip_role_name='originator',
                    event__generic_status__generic_status_name='incomplete',
                    audio_clip_tone_id=audio_clip_tone_id,
                ).order_by('id').first()

                latest_audio_clip = AudioClips.objects.filter(
                    generic_status__generic_status_name='ok',
                    audio_clip_role__audio_clip_role_name='originator',
                    event__generic_status__generic_status_name='incomplete',
                    audio_clip_tone_id=audio_clip_tone_id,
                ).order_by('id').last()

                if earliest_audio_clip is None or latest_audio_clip is None:

                    raise ValueError('Either test rows have not been set up properly, or rules for excluding tones in RealisticBulkData has changed.')

                minimum_datetimes.append(earliest_audio_clip.when_created)
                minimum_datetimes.append(latest_audio_clip.when_created)

                for minimum_datetime in minimum_datetimes:

                    result = self._query_1(
                        current_user_id=target_user.id,
                        audio_clip_tone_id=audio_clip_tone_id,
                        when_created=minimum_datetime,
                    )

                    is_row_count_expected = len(result['query_result']) > 0

                    if is_row_count_expected is True and result['time_elapsed_ms'] < minimum_time_elapsed_ms:

                        print('Good')
                        print({
                            'audio_clip_tone_id': audio_clip_tone_id,
                            'target_user_username': target_user.username,
                            'minimum_datetime': minimum_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                            'time_elapsed_ms': result['time_elapsed_ms'],
                        })

                        test_pass_count += 1

                        continue

                    print('\n')

                    if show_test_failed_query is True:

                        print(result['raw_query'])

                    print({
                        'is_row_count_expected': is_row_count_expected,
                        'rows_fetched': len(result['query_result']),
                        'audio_clip_tone_id': audio_clip_tone_id,
                        'target_user_username': target_user.username,
                        'minimum_datetime': minimum_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                        'time_elapsed_ms': result['time_elapsed_ms'],
                    })
                    print('\n')

                    test_fail_count += 1

            #expect rows matching tone to not exist
            for audio_clip_tone_id in excluded_audio_clip_tone_ids:

                #arbitrary start time, 10 years
                minimum_datetime = get_datetime_now() - timedelta(weeks=521)

                result = self._query_1(
                    current_user_id=target_user.id,
                    audio_clip_tone_id=audio_clip_tone_id,
                    when_created=minimum_datetime,
                )

                is_row_count_expected = len(result['query_result']) == 0

                if is_row_count_expected is True and result['time_elapsed_ms'] < minimum_time_elapsed_ms:

                    print('Good')
                    print({
                        'audio_clip_tone_id': audio_clip_tone_id,
                        'target_user_username': target_user.username,
                        'minimum_datetime': minimum_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                        'time_elapsed_ms': result['time_elapsed_ms'],
                    })

                    test_pass_count += 1

                    continue

                print('\n')

                if show_test_failed_query is True:

                    print(result['raw_query'])

                print({
                    'is_row_count_expected': is_row_count_expected,
                    'rows_fetched': len(result['query_result']),
                    'audio_clip_tone_id': audio_clip_tone_id,
                    'target_user_username': target_user.username,
                    'minimum_datetime': minimum_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    'time_elapsed_ms': result['time_elapsed_ms'],
                })
                print('\n')

                test_fail_count += 1

        print({
            'tests_passed': test_pass_count,
            'tests_failed': test_fail_count,
        })



























#==========================================================================
#===========================POTENTIALLY OUTDATED===========================
#==========================================================================



#CAUTION: optimisation tests can be out-of-date
#using TransactionTestCase to allow tests to run one by one
#conclusion from tests
    #little to no impact
        #kwargs or args
        #raw query if rows are not needed
    #medium impact
        #higher over lower batch_size
    #high impact
        #disable related triggers
            #trigger that also performs sql within itself is what slowed things down during bulk actions
#update: trigger is no longer used in production
@override_settings(
    DEBUG=True,
)
class BulkCreateOptimisation_TestCase(TestCase):

    #{test_function_name: anything}
    metrics = {}
    serialized_rollback = True


    @classmethod
    def setUpTestData(cls):

        cls.realistic_bulk_data_class = RealisticBulkData()

        result = cls.realistic_bulk_data_class.get_main_users_relative_to_entire_db()
        cls.main_users = result['main_users']
        cls.main_user_sets = result['main_user_sets']


    @classmethod
    def tearDownClass(cls):

        #print more beautifully
        for function_name in cls.metrics:

            print(function_name)
            print(cls.metrics[function_name])
            print('\n')

        try:
            cache.clear()
        except:
            pass

        with connection.cursor() as cursor:

            cursor.close()

        super().tearDownClass()


    def tearDown(cls):

        realistic_bulk_data_class = RealisticBulkData()

        realistic_bulk_data_class.modify_related_triggers(True)
        realistic_bulk_data_class.check_trigger('audio_clip_likes_dislikes', 'trigger_audio_clip_likes_dislikes', True)


    def create_users(self):

        print('Creating users.')

        users = []

        for x in range(self.minimum_main_user_quantity):

            users.append(
                get_user_model().objects.create_user(
                    username='user'+str(x),
                    email='user'+str(x)+'@gmail.com',
                    is_active=True,
                )
            )

        return users


    def create_originator_events(self, users):

        print('Creating events.')

        events = []
        
        datetime_now = get_datetime_now()
        generic_status = GenericStatuses.objects.get(generic_status_name='incomplete')

        for user in users:

            for x in range(self.originator_quantity_per_user):

                events.append(
                    Events(
                        None,
                        "An event by " + user.username,
                        generic_status.id,
                        user.id,
                        datetime_now,
                        datetime_now,
                    )
                )

        return Events.objects.bulk_create(events)


    def create_originator_audio_clips(self, events):

        print('Creating audio_clips.')

        audio_clips = []
        datetime_now = get_datetime_now()
        audio_clip_tone = AudioClipTones.objects.first()
        audio_clip_role = AudioClipRoles.objects.get(audio_clip_role_name='originator')
        generic_status = GenericStatuses.objects.get(generic_status_name='ok')

        for event in events:

            audio_clips.append(
                AudioClips(
                    None,
                    event.created_by.id,
                    audio_clip_role.id,
                    audio_clip_tone.id,
                    event.id,
                    generic_status.id,
                    '',
                    10,
                    [],
                    self.minimum_main_user_quantity,
                    0,
                    1,
                    False,
                    datetime_now,
                    datetime_now,
                )
            )

        return AudioClips.objects.bulk_create(audio_clips)


    def _create_audio_clip_likes_dislikes(self, users, audio_clips, batch_size, is_single_bulk_create):

        print('Creating audio_clip_likes_dislikes.')

        audio_clip_likes_dislikes = []
        final_rows = []
        datetime_now = get_datetime_now()

        #minimise the impact of having more if-statements on benchmark

        if is_single_bulk_create is True:

            for user in users:

                for audio_clip in audio_clips:

                    audio_clip_likes_dislikes.append(
                        AudioClipLikesDislikes(
                            None,
                            user.id,
                            audio_clip.id,
                            True,
                            datetime_now,
                            datetime_now,
                        )
                    )

            print(f'Size (bytes) of all AudioClipLikesDislikes, args, before bulk_create(): {sys.getsizeof(audio_clip_likes_dislikes)}')

            final_rows = AudioClipLikesDislikes.objects.bulk_create(
                audio_clip_likes_dislikes,
                batch_size=batch_size
            )

        else:

            for user in users:

                for audio_clip in audio_clips:

                    audio_clip_likes_dislikes.append(
                        AudioClipLikesDislikes(
                            None,
                            user.id,
                            audio_clip.id,
                            True,
                            datetime_now,
                            datetime_now,
                        )
                    )

                final_rows.extend(
                    AudioClipLikesDislikes.objects.bulk_create(
                        audio_clip_likes_dislikes,
                        batch_size=batch_size
                    )
                )
                audio_clip_likes_dislikes = []

        return final_rows


    def _create_audio_clip_likes_dislikes_kwargs(self, users, audio_clips, batch_size, is_single_bulk_create):

        print('Creating audio_clip_likes_dislikes.')

        audio_clip_likes_dislikes = []
        final_rows = []
        datetime_now = get_datetime_now()

        #minimise the impact of having more if-statements on benchmark

        if is_single_bulk_create is True:

            for user in users:

                for audio_clip in audio_clips:

                    audio_clip_likes_dislikes.append(
                        AudioClipLikesDislikes(
                            user=user,
                            audio_clip=audio_clip,
                            is_liked=True,
                        )
                    )

            print(f'Size (bytes) of all AudioClipLikesDislikes, kwargs, before bulk_create(): {sys.getsizeof(audio_clip_likes_dislikes)}')

            final_rows = AudioClipLikesDislikes.objects.bulk_create(
                audio_clip_likes_dislikes,
                batch_size=batch_size
            )

        else:

            for user in users:

                for audio_clip in audio_clips:

                    audio_clip_likes_dislikes.append(
                        AudioClipLikesDislikes(
                            user=user,
                            audio_clip=audio_clip,
                            is_liked=True,
                        )
                    )

                final_rows.extend(
                    AudioClipLikesDislikes.objects.bulk_create(
                        audio_clip_likes_dislikes,
                        batch_size=batch_size
                    )
                )
                audio_clip_likes_dislikes = []

        return final_rows


    def _create_audio_clip_likes_dislikes__raw(self, users, audio_clips, batch_size, must_reset_queries, use_trigger_but_skip):

        #important format notes
            #we use 'x' instead of whitespace-respecting '''x'''
                #there cannot be comma for last row in ', RETURNING'
                #can do '...,'[:len(full_sql)-1]

        #important efficiency notes
            #cursor.fetchall() returns tuples, e.g. [(9,),(10,),] for "RETURNING id;"
                #it is more efficient to write "current_row[0]" later, than to flatten this list of tuples

        print('Creating audio_clip_likes_dislikes.')

        def create_rows_in_db(full_sql, full_params):

            new_rows = None

            #remove the final ',' from final audio_clip row
            full_sql = full_sql[:len(full_sql)-1]
            full_sql += ' '

            #get PK only
            full_sql += 'RETURNING audio_clip_likes_dislikes.id;'

            if use_trigger_but_skip is True:

                with transaction.atomic():

                    with connection.cursor() as cursor:

                        cursor.execute('''SET LOCAL voicewake.skip_trigger_audio_clip_likes_dislikes = 1;''')
                        cursor.execute(full_sql, full_params)
                        new_rows = cursor.fetchall()

                        #ensure it's only 1 during transaction
                        check_sql = "SELECT NULLIF(current_setting('voicewake.skip_trigger_audio_clip_likes_dislikes'), NULL);"
                        cursor.execute(check_sql)
                        skip_trigger = int(cursor.fetchone()[0])
                        if skip_trigger == 0:
                            raise ValueError('This line should not be reached.')

                with connection.cursor() as cursor:

                    #ensure it's 0 outside of transaction above
                    check_sql = "SELECT NULLIF(current_setting('voicewake.skip_trigger_audio_clip_likes_dislikes'), NULL);"
                    cursor.execute(check_sql)
                    skip_trigger = int(cursor.fetchone()[0])
                    if skip_trigger == 1:
                        raise ValueError('Nope, not isolated.')

            else:

                with connection.cursor() as cursor:

                    cursor.execute(full_sql, full_params)
                    new_rows = cursor.fetchall()

            if must_reset_queries is True:

                reset_queries()

            return new_rows

        #start

        audio_clip_like_dislike_ids = []
        datetime_now = get_datetime_now()
        current_row_count = 0

        starter_sql = ''
        full_params = []

        if use_trigger_but_skip:

            #ensure conf parameter exists
            check_sql = "SELECT NULLIF(current_setting('voicewake.skip_trigger_audio_clip_likes_dislikes'), NULL);"

            with connection.cursor() as cursor:

                cursor.execute(check_sql)

                skip_trigger = int(cursor.fetchone()[0])

                if skip_trigger  == 1:

                    raise ValueError('Trigger for skipping at main system is unintentionally True.')

        starter_sql += 'INSERT INTO audio_clip_likes_dislikes (user_id, audio_clip_id, is_liked, when_created, last_modified) VALUES '

        full_sql = starter_sql

        for user in users:

            for audio_clip in audio_clips:

                full_sql += '(%s, %s, %s, %s, %s),'
                full_params.extend([
                    user.id,
                    audio_clip.id,
                    True,
                    datetime_now,
                    datetime_now
                ])

                current_row_count += 1

                if current_row_count == batch_size:

                    #batch size reached

                    #execute
                    new_audio_clip_like_dislike_ids = create_rows_in_db(full_sql, full_params)
                    audio_clip_like_dislike_ids.extend(new_audio_clip_like_dislike_ids)

                    #reset
                    full_sql = starter_sql
                    full_params = []
                    current_row_count = 0

        #handle any remaining rows

        if current_row_count > 0:

            #batch size reached

            #execute
            new_audio_clip_like_dislike_ids = create_rows_in_db(full_sql, full_params)
            audio_clip_like_dislike_ids.extend(new_audio_clip_like_dislike_ids)

            #reset
            full_sql = starter_sql
            full_params = []
            current_row_count = 0

        return audio_clip_like_dislike_ids


    def _update_metrics(self, function_name, row_count, seconds, total_bytes):

        self.metrics.update({
            function_name: {
                'row_count': row_count,
                'seconds': seconds,
                'new_objects_size_in_bytes_after_insertion': total_bytes, #sys.getsizeof(var_name)
            }
        })


    def _update_bulk_quantity(self, new_value):

        self.bulk_quantity = new_value

        self.minimum_main_user_quantity = 10 * self.bulk_quantity
        self.originator_quantity_per_user = 20 * self.bulk_quantity
        self.audio_clip_like_dislike_quantity = self.minimum_main_user_quantity * self.originator_quantity_per_user


    def test_behaviour__does_bulk_create_load_into_memory_without_evaluation(self):

        #container hangs at bulk_quantity = 10
        self._update_bulk_quantity(5)

        users = self.create_users()
        reset_queries()
        events = self.create_originator_events(users)
        reset_queries()
        audio_clips = self.create_originator_audio_clips(events)
        reset_queries()

        print('Creating audio_clip_likes_dislikes.')

        audio_clip_likes_dislikes = []
        datetime_now = get_datetime_now()

        for audio_clip in audio_clips:

            for user in users:

                audio_clip_likes_dislikes.append(
                    AudioClipLikesDislikes(
                        None,
                        user.id,
                        audio_clip.id,
                        True,
                        datetime_now,
                        datetime_now,
                    )
                )

        print('Object count: ' + str(len(audio_clip_likes_dislikes)))

        print('Only model objects before bulk_create: ' + str(sys.getsizeof(audio_clip_likes_dislikes)))

        audio_clip_likes_dislikes = AudioClipLikesDislikes.objects.bulk_create(
            audio_clip_likes_dislikes,
            batch_size=math.ceil(len(audio_clip_likes_dislikes) * 0.10)
        )

        print('After bulk_create: ' + str(sys.getsizeof(audio_clip_likes_dislikes)))

        print('Object count: ' + str(len(audio_clip_likes_dislikes)))

        len(audio_clip_likes_dislikes)

        print('After forced evaluation: ' + str(sys.getsizeof(audio_clip_likes_dislikes)))


    def test_one_bulk_create__high_batch_size(self):

        stopwatch = Stopwatch()

        users = self.create_users()
        events = self.create_originator_events(users)
        audio_clips = self.create_originator_audio_clips(events)

        stopwatch.start()
        audio_clip_likes_dislikes = self._create_audio_clip_likes_dislikes(users, audio_clips, self.high_batch_size, True)
        stopwatch.stop()

        self._update_metrics(
            get_current_function_name(),
            len(audio_clip_likes_dislikes),
            stopwatch.diff_seconds(),
            sys.getsizeof(audio_clip_likes_dislikes),
        )


    def test_one_bulk_create__high_batch_size__kwargs(self):

        stopwatch = Stopwatch()

        users = self.create_users()
        events = self.create_originator_events(users)
        audio_clips = self.create_originator_audio_clips(events)

        stopwatch.start()
        audio_clip_likes_dislikes = self._create_audio_clip_likes_dislikes_kwargs(users, audio_clips, self.high_batch_size, True)
        stopwatch.stop()

        self._update_metrics(
            get_current_function_name(),
            len(audio_clip_likes_dislikes),
            stopwatch.diff_seconds(),
            sys.getsizeof(audio_clip_likes_dislikes),
        )


    def test_one_bulk_create__reset_queries__low_batch_size(self):

        stopwatch = Stopwatch()

        users = self.create_users()
        reset_queries()
        events = self.create_originator_events(users)
        reset_queries()
        audio_clips = self.create_originator_audio_clips(events)
        reset_queries()

        stopwatch.start()
        audio_clip_likes_dislikes = self._create_audio_clip_likes_dislikes(users, audio_clips, self.low_batch_size, True)
        stopwatch.stop()
        reset_queries()

        self._update_metrics(
            get_current_function_name(),
            len(audio_clip_likes_dislikes),
            stopwatch.diff_seconds(),
            sys.getsizeof(audio_clip_likes_dislikes),
        )


    def test_one_bulk_create__reset_queries__high_batch_size(self):

        stopwatch = Stopwatch()

        users = self.create_users()
        reset_queries()
        events = self.create_originator_events(users)
        reset_queries()
        audio_clips = self.create_originator_audio_clips(events)
        reset_queries()

        stopwatch.start()
        audio_clip_likes_dislikes = self._create_audio_clip_likes_dislikes(users, audio_clips, self.high_batch_size, True)
        stopwatch.stop()
        reset_queries()

        self._update_metrics(
            get_current_function_name(),
            len(audio_clip_likes_dislikes),
            stopwatch.diff_seconds(),
            sys.getsizeof(audio_clip_likes_dislikes),
        )


    def test_one_bulk_create__reset_queries__high_batch_size__remove_trigger(self):

        stopwatch = Stopwatch()
        realistic_bulk_data_class = RealisticBulkData()

        users = self.create_users()
        reset_queries()
        events = self.create_originator_events(users)
        reset_queries()
        audio_clips = self.create_originator_audio_clips(events)
        reset_queries()

        realistic_bulk_data_class.check_trigger('audio_clip_likes_dislikes', 'trigger_audio_clip_likes_dislikes', True)
        realistic_bulk_data_class.modify_related_triggers(False)
        realistic_bulk_data_class.check_trigger('audio_clip_likes_dislikes', 'trigger_audio_clip_likes_dislikes', False)

        stopwatch.start()
        audio_clip_likes_dislikes = self._create_audio_clip_likes_dislikes(users, audio_clips, self.high_batch_size, True)
        stopwatch.stop()
        reset_queries()

        self._update_metrics(
            get_current_function_name(),
            len(audio_clip_likes_dislikes),
            stopwatch.diff_seconds(),
            sys.getsizeof(audio_clip_likes_dislikes),
        )


    def test_many_bulk_create__reset_queries__high_batch_size__remove_trigger(self):

        stopwatch = Stopwatch()
        realistic_bulk_data_class = RealisticBulkData()

        users = self.create_users()
        reset_queries()
        events = self.create_originator_events(users)
        reset_queries()
        audio_clips = self.create_originator_audio_clips(events)
        reset_queries()

        realistic_bulk_data_class.check_trigger('audio_clip_likes_dislikes', 'trigger_audio_clip_likes_dislikes', True)
        realistic_bulk_data_class.modify_related_triggers(False)
        realistic_bulk_data_class.check_trigger('audio_clip_likes_dislikes', 'trigger_audio_clip_likes_dislikes', False)

        stopwatch.start()
        audio_clip_likes_dislikes = self._create_audio_clip_likes_dislikes(users, audio_clips, self.high_batch_size, False)
        stopwatch.stop()
        reset_queries()

        self._update_metrics(
            get_current_function_name(),
            len(audio_clip_likes_dislikes),
            stopwatch.diff_seconds(),
            sys.getsizeof(audio_clip_likes_dislikes),
        )


    def test_raw_sql__high_batch_size__return_pk_only(self):

        stopwatch = Stopwatch()
        realistic_bulk_data_class = RealisticBulkData()

        users = self.create_users()
        events = self.create_originator_events(users)
        audio_clips = self.create_originator_audio_clips(events)

        realistic_bulk_data_class.check_trigger('audio_clip_likes_dislikes', 'trigger_audio_clip_likes_dislikes', True)

        stopwatch.start()
        audio_clip_likes_dislikes = self._create_audio_clip_likes_dislikes__raw(users, audio_clips, self.high_batch_size, False, False)
        stopwatch.stop()

        self._update_metrics(
            get_current_function_name(),
            len(audio_clip_likes_dislikes),
            stopwatch.diff_seconds(),
            sys.getsizeof(audio_clip_likes_dislikes),
        )


    def test_raw_sql__reset_queries__high_batch_size__return_pk_only(self):

        stopwatch = Stopwatch()
        realistic_bulk_data_class = RealisticBulkData()

        users = self.create_users()
        reset_queries()
        events = self.create_originator_events(users)
        reset_queries()
        audio_clips = self.create_originator_audio_clips(events)
        reset_queries()

        realistic_bulk_data_class.check_trigger('audio_clip_likes_dislikes', 'trigger_audio_clip_likes_dislikes', True)

        stopwatch.start()
        audio_clip_likes_dislikes = self._create_audio_clip_likes_dislikes__raw(users, audio_clips, self.high_batch_size, True, False)
        stopwatch.stop()
        reset_queries()

        self._update_metrics(
            get_current_function_name(),
            len(audio_clip_likes_dislikes),
            stopwatch.diff_seconds(),
            sys.getsizeof(audio_clip_likes_dislikes),
        )


    def test_raw_sql__reset_queries__high_batch_size__return_pk_only__remove_trigger(self):

        stopwatch = Stopwatch()
        realistic_bulk_data_class = RealisticBulkData()

        users = self.create_users()
        reset_queries()
        events = self.create_originator_events(users)
        reset_queries()
        audio_clips = self.create_originator_audio_clips(events)
        reset_queries()

        realistic_bulk_data_class.check_trigger('audio_clip_likes_dislikes', 'trigger_audio_clip_likes_dislikes', True)
        realistic_bulk_data_class.modify_related_triggers(False)
        realistic_bulk_data_class.check_trigger('audio_clip_likes_dislikes', 'trigger_audio_clip_likes_dislikes', False)

        stopwatch.start()
        audio_clip_likes_dislikes = self._create_audio_clip_likes_dislikes__raw(users, audio_clips, self.high_batch_size, True, False)
        stopwatch.stop()
        reset_queries()

        self._update_metrics(
            get_current_function_name(),
            len(audio_clip_likes_dislikes),
            stopwatch.diff_seconds(),
            sys.getsizeof(audio_clip_likes_dislikes),
        )


    def test_raw_sql__reset_queries__high_batch_size__use_trigger_but_skip(self):

        stopwatch = Stopwatch()

        users = self.create_users()
        reset_queries()
        events = self.create_originator_events(users)
        reset_queries()
        audio_clips = self.create_originator_audio_clips(events)
        reset_queries()

        stopwatch.start()
        audio_clip_likes_dislikes = self._create_audio_clip_likes_dislikes__raw(users, audio_clips, self.high_batch_size, True, True)
        stopwatch.stop()
        reset_queries()

        self._update_metrics(
            get_current_function_name(),
            len(audio_clip_likes_dislikes),
            stopwatch.diff_seconds(),
            sys.getsizeof(audio_clip_likes_dislikes),
        )




#==========================================================================
#===========================POTENTIALLY OUTDATED===========================
#==========================================================================


























































