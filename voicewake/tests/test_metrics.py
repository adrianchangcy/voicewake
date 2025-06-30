from time import sleep
from django.test import TestCase, Client, TransactionTestCase, SimpleTestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db import connection
from django.core.cache import cache
from django.db.models import Case, Value, When, Sum, Q, F, Count, BooleanField
from django.conf import settings
from django.db import connection, reset_queries

from voicewake.models import *
from voicewake.services import *
from voicewake.factories import *

import math
from typing import Literal
import inspect
import time
import threading







#good balance of rows with same dates will test indexing better
#if you have too many rows to the point where it's unrealistic, space out data creation with time.sleep(1)
class RealisticBulkData():

    def __init__(
        self,
        batch_quantity=1,
        db_batch_size=500,
    ):

        self.batch_quantity = batch_quantity
        self.db_batch_size = db_batch_size

        self.user_ids = get_user_model().objects.all().exclude(is_superuser=True).order_by('id').values_list('id', flat=True)

        #4 users (e.g. block/blocked/mutualblock/none), scenarios in 3 ranges (earliest/middle/latest users), i.e. 4*3
        self.unique_user_ids = {
            'earliest_user_ids': [],
            'middle_user_ids': [],
            'latest_user_ids': [],
        }

        #increase this as needed
        self.minimum_unique_users_per_range = 4

        #current minimum for user_quantity is due to requiring unique identifiable users
        self.user_quantity = (len(self.unique_user_ids) * self.minimum_unique_users_per_range) * batch_quantity
        self.user_prefix = "testuser"
        self.user_count = 0
        self.new_users = []
        self.audio_file = os.path.join(
            settings.BASE_DIR,
            'voicewake/tests/file_samples/audio_ok_1.mp3'
        )

        #keep this lower so you can frequently mix and match the creating phase for more realistic data
        self.event_quantity = 5 * batch_quantity

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

        #check existing db
        for index in self.excluded_audio_clip_tones_indexes:

            row_count = AudioClips.objects.filter(audio_clip_tone_id=self.audio_clip_tones[index].id).count()

            if row_count > 0:

                raise ValueError('''
                    Tones to be excluded has unexpected rows in existing db.
                    This means your audio_clip_tones were updated.
                    Please recreate db.
                ''')

        self.like_count = 0
        self.dislike_count = 0
        self.like_ratio = 0


    def _check_ready(self):

        if len(self.new_users) == 0:

            raise ValueError('No users created. Call .prepare_users() first.')
        
        elif len(self.new_users) < 2:

            raise ValueError('Minimum 2 users required.')

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


    def create_new_users(self):

        #reset so it doesn't become exponential
        self.new_users = []

        user_count = 0

        if get_user_model().objects.filter(username_lowercase__startswith=self.user_prefix).exists() is True:

            latest_test_user = get_user_model().objects.filter(email_lowercase__startswith=self.user_prefix.lower()).order_by('-date_joined')[:1]
            latest_test_user = latest_test_user[0]

            print('Found latest test user by email: ' + latest_test_user.email_lowercase)

            #separate "99" from "testuser99@gmail.com"
            latest_user_index = latest_test_user.email_lowercase.split(self.user_prefix)
            latest_user_index = latest_user_index[1]
            latest_user_index = latest_user_index.split('@gmail.com')
            latest_user_index = int(latest_user_index[0])

            #if latest user is username99, we set starting count to 100 when creating new users
            user_count = latest_user_index + 1

        #create users

        for x in range(user_count, user_count+self.user_quantity):

            new_username = self.user_prefix + str(x)
            new_email = new_username + '@gmail.com'

            self.new_users.append(
                get_user_model().objects.create_user(
                    username=new_username,
                    email=new_email,
                    is_active=True,
                )
            )

            print('Created test user: ' + self.new_users[-1].username)


    def _determine_unique_users_after_no_new_users_left_to_create(self):

        #venn diagram
        #D[  A  ][C][  B  ]D
        #we want earliest/middle/latest ranges to look for dip in performance from no/misconfigured indexing in db
        #currently only need 4 users for every range, e.g.:
            #A blocks everyone
            #everyone blocks B
            #C blocks everyone and everyone blocks C
            #no blocking for D

        #earliest

        for x in range(self.minimum_unique_users_per_range):

            self.unique_user_ids['earliest_user_ids'].append(self.user_ids[x])

        #middle

        middle_index = math.floor(len(self.user_ids)/2)
        self.unique_user_ids['middle_user_ids'] = [
            self.user_ids[middle_index-2],
            self.user_ids[middle_index-1],
            self.user_ids[middle_index],
            self.user_ids[middle_index+1],
        ]

        #latest

        for x in range(self.minimum_unique_users_per_range):

            #offset x by +1
            index = len(self.user_ids)-(x+1)

            self.unique_user_ids['latest_user_ids'].append(self.user_ids[index])

        total_user_count = (
            len(self.unique_user_ids['earliest_user_ids']) +
            len(self.unique_user_ids['middle_user_ids']) +
            len(self.unique_user_ids['latest_user_ids'])
        )

        if len(self.user_ids) < total_user_count:

            raise ValueError('Not enough users.')

        #update targeted users to make them easy to find
        #retire past unique users if they do not match with new ones
        #modify only username, so future bulk data creation can still rely on email for latest user index

        retired_earliest_index = get_user_model().objects.filter(username_lowercase__startswith='retired_earliest_').order_by('-username_lowercase')[:1]
        retired_middle_index = get_user_model().objects.filter(username_lowercase__startswith='retired_middle_').order_by('-username_lowercase')[:1]
        retired_latest_index = get_user_model().objects.filter(username_lowercase__startswith='retired_latest_').order_by('-username_lowercase')[:1]

        if len(retired_earliest_index) == 0:

            retired_earliest_index = 0

        else:

            retired_earliest_index = int(retired_earliest_index[0].username_lowercase.split('retired_earliest_')[1]) + 1

        if len(retired_middle_index) == 0:

            retired_middle_index = 0

        else:

            retired_middle_index = int(retired_middle_index[0].username_lowercase.split('retired_middle_')[1]) + 1

        if len(retired_latest_index) == 0:

            retired_latest_index = 0

        else:

            retired_latest_index = int(retired_latest_index[0].username_lowercase.split('retired_latest_')[1]) + 1

        #start updating usernames

        for user_id in self.unique_user_ids['earliest_user_ids']:

            try:

                past_unique_user = get_user_model().objects.get(username_lowercase=f'earliest_{retired_earliest_index}')

                if past_unique_user.id != user_id:

                    past_unique_user.username = f'retired_earliest_{retired_earliest_index}'
                    past_unique_user.username_lowercase = f'retired_earliest_{retired_earliest_index}'
                    past_unique_user.save()

            except get_user_model().DoesNotExist:

                get_user_model().objects.filter(pk=user_id).update(
                    username=f'earliest_{retired_earliest_index}', username_lowercase=f'earliest_{retired_earliest_index}'
                )

            retired_earliest_index += 1

        for user_id in self.unique_user_ids['middle_user_ids']:

            try:

                past_unique_user = get_user_model().objects.get(username_lowercase=f'middle_{retired_middle_index}')

                if past_unique_user.id != user_id:

                    past_unique_user.username = f'retired_middle_{retired_middle_index}'
                    past_unique_user.username_lowercase = f'retired_middle_{retired_middle_index}'
                    past_unique_user.save()

            except get_user_model().DoesNotExist:

                get_user_model().objects.filter(pk=user_id).update(
                    username=f'middle_{retired_middle_index}', username_lowercase=f'middle_{retired_middle_index}'
                )

            retired_middle_index += 1

        for user_id in self.unique_user_ids['latest_user_ids']:

            try:

                past_unique_user = get_user_model().objects.get(username_lowercase=f'latest_{retired_latest_index}')

                if past_unique_user.id != user_id:

                    past_unique_user.username = f'retired_latest_{retired_latest_index}'
                    past_unique_user.username_lowercase = f'retired_latest_{retired_latest_index}'
                    past_unique_user.save()

            except get_user_model().DoesNotExist:

                get_user_model().objects.filter(pk=user_id).update(
                    username=f'latest_{retired_latest_index}', username_lowercase=f'latest_{retired_latest_index}'
                )

            retired_latest_index += 1


    @staticmethod
    def get_unique_user_ids():

        realistic_bulk_data_class = RealisticBulkData()

        unique_user_ids = {
            'earliest_user_ids': [],
            'middle_user_ids': [],
            'latest_user_ids': [],
        }

        #earliest

        for x in range(realistic_bulk_data_class.minimum_unique_users_per_range):

            target_user = get_user_model().objects.get(username=f'earliest_{x}')
            unique_user_ids['earliest_user_ids'].append(target_user.id)

            target_user = get_user_model().objects.get(username=f'middle_{x}')
            unique_user_ids['middle_user_ids'].append(target_user.id)

            target_user = get_user_model().objects.get(username=f'latest_{x}')
            unique_user_ids['latest_user_ids'].append(target_user.id)

        return unique_user_ids


    def prepare_like_dislike_estimate(self):

        if self.user_quantity < 10:

            raise ValueError('To keep things simple, please maintain a minimum of 10.')

        if len(self.new_users) == 0:

            raise ValueError('No users. Call .create_new_users() first.')

        #to prevent full exponential scaling, allow an amount of users to not vote at every audio_clip

        #len(users) must not be divisible by (like_count + dislike_count), else one user has only likes, the other dislikes, etc.
        #this is easily achieved by doing (len(users)/2)+1
        #better +1 than -1, since having too few also means some users have only likes/dislikes
        self.like_count = math.ceil(len(self.new_users) * 0.25)
        self.dislike_count = math.ceil(len(self.new_users) * 0.5) + 1

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

                    current_user = self.new_users[user_index]

                except IndexError:

                    user_index = 0
                    current_user = self.new_users[user_index]

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

                    current_user = self.new_users[user_index]

                except IndexError:

                    user_index = 0
                    current_user = self.new_users[user_index]

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


    def create_user_blocks(self):

        user_ids = []
        unique_user_ids = None

        #get unique user_ids

        try:

            unique_user_ids = self.get_unique_user_ids()

        except get_user_model().DoesNotExist:

            self._determine_unique_users_after_no_new_users_left_to_create()
            unique_user_ids = self.unique_user_ids

        #take out users that must not have blocks

        excluded_user_ids = [
            unique_user_ids['earliest_user_ids'][3],
            unique_user_ids['middle_user_ids'][3],
            unique_user_ids['latest_user_ids'][3],
        ]

        for user_id in self.user_ids:

            matched_excluded_user_id_index = None

            for index, excluded_user_id in enumerate(excluded_user_ids):

                if user_id == excluded_user_id:

                    matched_excluded_user_id_index = index

            if matched_excluded_user_id_index is not None:

                excluded_user_ids.pop(matched_excluded_user_id_index)
                continue

            user_ids.append(user_id)

        #for UserBlocks, you cannot block yourself
        #instead of exponential if-statements checking for it, we only check once after all for-loops

        user_block_rows = []

        #block every user
        for user_id in user_ids:

            user_block_rows.append(
                UserBlocks(user_id=unique_user_ids['earliest_user_ids'][0], blocked_user_id=user_id)
            )
            user_block_rows.append(
                UserBlocks(user_id=unique_user_ids['middle_user_ids'][0], blocked_user_id=user_id)
            )
            user_block_rows.append(
                UserBlocks(user_id=unique_user_ids['latest_user_ids'][0], blocked_user_id=user_id)
            )

        #blocked by every user
        for user_id in user_ids:

            user_block_rows.append(
                UserBlocks(user_id=user_id, blocked_user_id=unique_user_ids['earliest_user_ids'][1])
            )
            user_block_rows.append(
                UserBlocks(user_id=user_id, blocked_user_id=unique_user_ids['middle_user_ids'][1])
            )
            user_block_rows.append(
                UserBlocks(user_id=user_id, blocked_user_id=unique_user_ids['latest_user_ids'][1])
            )

        #mutual blocking
        for user_id in user_ids:

            user_block_rows.append(
                UserBlocks(user_id=unique_user_ids['earliest_user_ids'][2], blocked_user_id=user_id)
            )
            user_block_rows.append(
                UserBlocks(user_id=unique_user_ids['middle_user_ids'][2], blocked_user_id=user_id)
            )
            user_block_rows.append(
                UserBlocks(user_id=unique_user_ids['latest_user_ids'][2], blocked_user_id=user_id)
            )
            user_block_rows.append(
                UserBlocks(user_id=user_id, blocked_user_id=unique_user_ids['earliest_user_ids'][2])
            )
            user_block_rows.append(
                UserBlocks(user_id=user_id, blocked_user_id=unique_user_ids['middle_user_ids'][2])
            )
            user_block_rows.append(
                UserBlocks(user_id=user_id, blocked_user_id=unique_user_ids['latest_user_ids'][2])
            )

        #check for self-blocks

        index = 0

        while index < len(user_block_rows):

            if user_block_rows[index].user_id == user_block_rows[index].blocked_user_id:

                user_block_rows.pop(index)

            else:

                index += 1

        #create rows
        #rely on unique constraint and ignore_conflicts=True to remove duplicates
        UserBlocks.objects.bulk_create(user_block_rows, ignore_conflicts=True, batch_size=self.db_batch_size)


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

            for user in self.new_users:

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
                        audio_duration_s=10,
                        audio_volume_peaks=[],
                        is_banned=False,
                    )
                )

                #users who have skipped before
                #we refer to existing user in event_reply_queues if is_replying=True, so we don't have the same user skipping and replying

                if skipped_by_users is True:

                    for user in self.new_users:

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

        for user in self.new_users:

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
                    audio_duration_s=10,
                    audio_volume_peaks=[],
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
                locked_for_user=self.new_users[0],
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
                        locked_for_user=self.new_users[index+1],
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

            for user in self.new_users:

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
                        None,
                        event.created_by.id,
                        self.audio_clip_roles['originator'].id,
                        audio_clip_tone.id,
                        event.id,
                        self.generic_statuses['ok'].id,
                        self.audio_file,
                        10,
                        [],
                        False,
                        datetime_now,
                        datetime_now,
                    )
                )

                #for responder, we +1 self.new_users until the end, then restart from 0
                #originator and responder cannot be the same
                responder = None

                try:

                    #use this statement to check for IndexError
                    #also might as well +=1 if users are the same
                    if self.new_users[responder_user_index] == event.created_by.pk:

                        responder_user_index += 1

                except IndexError:

                    #out of range, restart
                    responder_user_index = 0

                    if self.new_users[responder_user_index] == event.created_by.pk:

                        responder_user_index += 1

                responder = self.new_users[responder_user_index]
                responder_user_index += 1

                responder_audio_clips.append(
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
                        False,
                        datetime_now,
                        datetime_now,
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

            for user in self.new_users:

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
                        audio_duration_s=10,
                        audio_volume_peaks=[],
                        is_banned=is_originator_banned,
                    )
                )

                if has_responder is False:

                    continue

                #for responder, we +1 self.new_users until the end, then restart from 0
                #originator and responder cannot be the same
                responder = None

                try:

                    #use this statement to check for IndexError
                    #also might as well +=1 if users are the same
                    if self.new_users[responder_user_index] == event.created_by.pk:

                        responder_user_index += 1

                except IndexError:

                    #out of range, restart
                    responder_user_index = 0

                    if self.new_users[responder_user_index] == event.created_by.pk:

                        responder_user_index += 1

                responder = self.new_users[responder_user_index]
                responder_user_index += 1

                responder_audio_clips.append(
                    AudioClips(
                        user=responder,
                        audio_clip_role=self.audio_clip_roles['responder'],
                        audio_clip_tone=audio_clip_tone,
                        event=event,
                        generic_status=responder_audio_clip_generic_status,
                        audio_file=self.audio_file,
                        audio_duration_s=10,
                        audio_volume_peaks=[],
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
                    None,
                    audio_clip=audio_clip,
                    like_count=0,
                    dislike_count=0,
                    like_ratio=0,
                )
            )

        for audio_clip in responder_audio_clips:

            responder_audio_clip_metrics.append(
                AudioClipMetrics(
                    None,
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


    #if you want more rows, specify max_randomness_iteration_count (5 is good, be careful of more because it's exponential)
    #cmd:
        #python manage.py shell -c "from voicewake.tests.test_metrics import RealisticBulkData; RealisticBulkData.sample_run(10, True);"
    @staticmethod
    def sample_run(max_randomness_iteration_count=5, use_threads=True):

        #add anything here for rows to be "earlier", beneficial for tests

        #user * blocks * blocked * is_originator(many/few/0) * is_responder(many/few/0)
        #ensure these special users are identifiable and retrievable, via username/email

        #this improves realism of randomness
        current_randomness_iteration_count = 0

        realistic_bulk_data_class = RealisticBulkData(
            batch_quantity=1,
            db_batch_size=500,
        )

        while current_randomness_iteration_count < max_randomness_iteration_count:

            #create users per while-loop for realistic non-hyperactive users
            realistic_bulk_data_class.create_new_users()
            realistic_bulk_data_class.prepare_like_dislike_estimate()

            if use_threads is False:

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

        #-1 since originator cannot skip own events
        self.assertEqual(
            len(result['user_events']),
            (
                (len(realistic_bulk_data_class.audio_clip_tones) - len(realistic_bulk_data_class.excluded_audio_clip_tones_indexes))
                * realistic_bulk_data_class.event_quantity
                * len(realistic_bulk_data_class.new_users)
                #-1 because we simply skip creation if originator == current_user
                * (len(realistic_bulk_data_class.new_users) - 1)
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








#instead of using TransactionTestCase, do use_threads=False for .sample_run() then use TestCase
@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    DEBUG=True,
)
class RealisticBulkData_SampleRun_TestCase(TestCase):

    def test_realistic_bulk_data__small_sample_run(self):

        realistic_bulk_data_class = RealisticBulkData()
        realistic_bulk_data_class.sample_run(max_randomness_iteration_count=1, use_threads=False)

        #test repeated calls
        realistic_bulk_data_class = RealisticBulkData()
        realistic_bulk_data_class.create_new_users()
        realistic_bulk_data_class.sample_run(max_randomness_iteration_count=1, use_threads=False)


    def test_realistic_bulk_data__small_sample_run__tone_not_reduced(self):

        realistic_bulk_data_class = RealisticBulkData()
        realistic_bulk_data_class.sample_run(max_randomness_iteration_count=1, use_threads=False,)

        #test repeated calls
        realistic_bulk_data_class = RealisticBulkData()
        realistic_bulk_data_class.sample_run(max_randomness_iteration_count=1, use_threads=False,)







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
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    DEBUG=True,
)
class BulkCreateOptimisation_TestCase(TestCase):

    #{test_function_name: anything}
    metrics = {}
    serialized_rollback = True

    @classmethod
    def setUp(cls):

        cls.bulk_quantity = 5

        cls.low_batch_size = 100
        cls.high_batch_size = 500

        cls.user_quantity = 10 * cls.bulk_quantity
        cls.originator_quantity_per_user = 20 * cls.bulk_quantity
        cls.audio_clip_like_dislike_quantity = cls.user_quantity * cls.originator_quantity_per_user


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

        for x in range(self.user_quantity):

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
                    self.user_quantity,
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

        self.user_quantity = 10 * self.bulk_quantity
        self.originator_quantity_per_user = 20 * self.bulk_quantity
        self.audio_clip_like_dislike_quantity = self.user_quantity * self.originator_quantity_per_user


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


















#this test handles full validation and performance
    #easier to do it here than to duplicate into test_apis and test_metrics
    #uses RealisticBulkData
#logic behaviours:
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
class BrowseEvents_TestCase(TestCase):

    #{test_function_name: anything}
    metrics = {}

    @classmethod
    def setUp(cls):

        cls.unique_users = []

        cls.realistic_bulk_data_class = RealisticBulkData()

        #get unique users
        unique_user_ids = cls.realistic_bulk_data_class.get_unique_user_ids()

        #only need 1 user from each category
        for category_name in unique_user_ids:

            cls.unique_users.append(
                get_user_model().objects.get(pk=unique_user_ids[category_name][0])
            )


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
    def _general_row_check(self, response_data, audio_clip_role_name:Literal['originator','responder'],):

        opposite_audio_clip_role_name = 'originator'

        if opposite_audio_clip_role_name == audio_clip_role_name:

            opposite_audio_clip_role_name = 'responder'

        previous_row = response_data['data'][0]

        #first checks for precedence
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

            #smaller id
            self.assertLess(
                current_row[audio_clip_role_name][0]['id'],
                previous_row[audio_clip_role_name][0]['id'],
            )

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


    def test_browse_events__main_page(self, minimum_time_elapsed_ms=200):

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

        test_index = 0

        audio_clip_tone_ids = expected_audio_clip_tone_ids + excluded_audio_clip_tone_ids

        is_excluded_audio_clip_tone = False

        for unique_user in self.unique_users:

            self.login(unique_user)

            for audio_clip_role_name in ['originator', 'responder']:

                for audio_clip_tone_id_index, audio_clip_tone_id in audio_clip_tone_ids:

                    if (audio_clip_tone_id_index + 1) > len(expected_audio_clip_tone_ids):

                        is_excluded_audio_clip_tone = True

                    current_kwargs = {
                        'latest_or_best': 'latest',
                        'timeframe': 'all',
                        'audio_clip_role_name': audio_clip_role_name,
                        'audio_clip_tone_id': audio_clip_tone_id,
                        'next_or_back': 'next',
                    }

                    try:

                        loop_title = 'loop #' + str(test_index)

                        print(loop_title)

                        test_index += 1

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

                        self.assertEqual(len(response_data['data']), settings.EVENT_QUANTITY_PER_PAGE)

                        #check rows
                        self._general_row_check(response_data, audio_clip_role_name)

                        #keep this for next->back validation later
                        first_response_data = response_data['data'].copy()

                        #check tokens
                        self._general_cursor_token_check(response_data, audio_clip_role_name)

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

                        self.assertEqual(len(response_data['data']), settings.EVENT_QUANTITY_PER_PAGE)

                        #check rows
                        self._general_row_check(response_data, audio_clip_role_name)

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
                        self._general_row_check(response_data, audio_clip_role_name)

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

                        self.assertEqual(len(response_data['data']), 0)
                        self.assertEqual(response_data['next_token'], response_data['back_token'])
                        self.assertEqual(response_data['next_token'], cursor_token)

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
                        self._general_row_check(response_data, audio_clip_role_name)

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
                        #API next+token, expect 0 rows
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

                        self.assertEqual(len(response_data['data']), 0)
                        self.assertEqual(response_data['next_token'], response_data['back_token'])

                    except Exception as e:

                        print(current_kwargs)
                        print(f'is_excluded_audio_clip_tone: {is_excluded_audio_clip_tone}')
                        raise e


    def test_browse_events__other_user_page(self, minimum_time_elapsed_ms=200):

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

        test_index = 0

        audio_clip_tone_ids = expected_audio_clip_tone_ids + excluded_audio_clip_tone_ids

        is_excluded_audio_clip_tone = False

        for login_user in self.unique_users:

            self.login(login_user)

            for unique_user in self.unique_users:

                if unique_user.id == login_user.id:

                    #save users viewing their own page for another test case
                    continue

                for audio_clip_role_name in ['originator', 'responder']:

                    for audio_clip_tone_id_index, audio_clip_tone_id in audio_clip_tone_ids:

                        if (audio_clip_tone_id_index + 1) > len(expected_audio_clip_tone_ids):

                            is_excluded_audio_clip_tone = True

                        current_kwargs = {
                            'username': unique_user.username,
                            'latest_or_best': 'latest',
                            'timeframe': 'all',
                            'audio_clip_role_name': audio_clip_role_name,
                            'audio_clip_tone_id': audio_clip_tone_id,
                            'next_or_back': 'next',
                        }

                        try:

                            loop_title = 'loop #' + str(test_index)

                            print(loop_title)

                            test_index += 1

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

                            self.assertEqual(len(response_data['data']), settings.EVENT_QUANTITY_PER_PAGE)

                            #check rows
                            self._general_row_check(response_data, audio_clip_role_name)

                            #keep this for next->back validation later
                            first_response_data = response_data['data'].copy()

                            #check tokens
                            self._general_cursor_token_check(response_data, audio_clip_role_name)

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

                            self.assertEqual(len(response_data['data']), settings.EVENT_QUANTITY_PER_PAGE)

                            #check rows
                            self._general_row_check(response_data, audio_clip_role_name)

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
                            self._general_row_check(response_data, audio_clip_role_name)

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

                            self.assertEqual(len(response_data['data']), 0)
                            self.assertEqual(response_data['next_token'], response_data['back_token'])
                            self.assertEqual(response_data['next_token'], cursor_token)

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
                            self._general_row_check(response_data, audio_clip_role_name)

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
                            #API next+token, expect 0 rows
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

                            self.assertEqual(len(response_data['data']), 0)
                            self.assertEqual(response_data['next_token'], response_data['back_token'])

                        except Exception as e:

                            print(current_kwargs)
                            print(f'is_excluded_audio_clip_tone: {is_excluded_audio_clip_tone}')
                            raise e


    #TODO: write extra APIs for guaranteeing "incomplete/completed" as originator, and "completed/deleted" as responder
    def test_browse_events__own_page(self, minimum_time_elapsed_ms=200):

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

        test_index = 0

        audio_clip_tone_ids = expected_audio_clip_tone_ids + excluded_audio_clip_tone_ids

        is_excluded_audio_clip_tone = False

        for unique_user in self.unique_users:

            self.login(unique_user)

            for audio_clip_role_name in ['originator', 'responder']:

                for audio_clip_tone_id_index, audio_clip_tone_id in audio_clip_tone_ids:

                    if (audio_clip_tone_id_index + 1) > len(expected_audio_clip_tone_ids):

                        is_excluded_audio_clip_tone = True

                    current_kwargs = {
                        'username': unique_user.username,
                        'latest_or_best': 'latest',
                        'timeframe': 'all',
                        'audio_clip_role_name': audio_clip_role_name,
                        'audio_clip_tone_id': audio_clip_tone_id,
                        'next_or_back': 'next',
                    }

                    try:

                        loop_title = 'loop #' + str(test_index)

                        print(loop_title)

                        test_index += 1

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

                        self.assertEqual(len(response_data['data']), settings.EVENT_QUANTITY_PER_PAGE)

                        #check rows
                        self._general_row_check(response_data, audio_clip_role_name)

                        #keep this for next->back validation later
                        first_response_data = response_data['data'].copy()

                        #check tokens
                        self._general_cursor_token_check(response_data, audio_clip_role_name)

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

                        self.assertEqual(len(response_data['data']), settings.EVENT_QUANTITY_PER_PAGE)

                        #check rows
                        self._general_row_check(response_data, audio_clip_role_name)

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
                        self._general_row_check(response_data, audio_clip_role_name)

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

                        self.assertEqual(len(response_data['data']), 0)
                        self.assertEqual(response_data['next_token'], response_data['back_token'])
                        self.assertEqual(response_data['next_token'], cursor_token)

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
                        self._general_row_check(response_data, audio_clip_role_name)

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
                        #API next+token, expect 0 rows
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

                        self.assertEqual(len(response_data['data']), 0)
                        self.assertEqual(response_data['next_token'], response_data['back_token'])

                    except Exception as e:

                        print(current_kwargs)
                        print(f'is_excluded_audio_clip_tone: {is_excluded_audio_clip_tone}')
                        raise e


    #TODO: write extra APIs for guaranteeing "incomplete/completed" as originator, and "completed/deleted" as responder
    def test_browse_events__own_likes_dislikes(self, minimum_time_elapsed_ms=200):

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

        test_index = 0

        audio_clip_tone_ids = expected_audio_clip_tone_ids + excluded_audio_clip_tone_ids

        is_excluded_audio_clip_tone = False

        for unique_user in self.unique_users:

            self.login(unique_user)

            for audio_clip_role_name in ['originator', 'responder']:

                for likes_or_dislikes in ['likes', 'dislikes']:

                    for audio_clip_tone_id_index, audio_clip_tone_id in audio_clip_tone_ids:

                        if (audio_clip_tone_id_index + 1) > len(expected_audio_clip_tone_ids):

                            is_excluded_audio_clip_tone = True

                        current_kwargs = {
                            'username': unique_user.username,
                            'latest_or_best': 'latest',
                            'timeframe': 'all',
                            'audio_clip_role_name': audio_clip_role_name,
                            'audio_clip_tone_id': audio_clip_tone_id,
                            'next_or_back': 'next',
                            'likes_or_dislikes': likes_or_dislikes,
                        }

                        try:

                            loop_title = 'loop #' + str(test_index)

                            print(loop_title)

                            test_index += 1

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

                            self.assertEqual(len(response_data['data']), settings.EVENT_QUANTITY_PER_PAGE)

                            #check rows
                            self._general_row_check(response_data, audio_clip_role_name)

                            #keep this for next->back validation later
                            first_response_data = response_data['data'].copy()

                            #check tokens
                            self._general_cursor_token_check(response_data, audio_clip_role_name)

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

                            self.assertEqual(len(response_data['data']), settings.EVENT_QUANTITY_PER_PAGE)

                            #check rows
                            self._general_row_check(response_data, audio_clip_role_name)

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
                            self._general_row_check(response_data, audio_clip_role_name)

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

                            self.assertEqual(len(response_data['data']), 0)
                            self.assertEqual(response_data['next_token'], response_data['back_token'])
                            self.assertEqual(response_data['next_token'], cursor_token)

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
                            self._general_row_check(response_data, audio_clip_role_name)

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
                            #API next+token, expect 0 rows
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

                            self.assertEqual(len(response_data['data']), 0)
                            self.assertEqual(response_data['next_token'], response_data['back_token'])

                        except Exception as e:

                            print(current_kwargs)
                            print(f'is_excluded_audio_clip_tone: {is_excluded_audio_clip_tone}')
                            raise e









    #DELETE FOLLOWING TESTS ONCE TESTS ABOVE ARE DONE


    def test_browse_events__no_audio_clip_tone(self):

        return

        metrics = {}
        stopwatch = Stopwatch()

        for unique_user in self.unique_users:

            self.login(unique_user)

            #==========
            #main page, only completed
            #==========

            latest_completed_kwargs = []
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

            #check test setup

            self.assertEqual(len(latest_completed_kwargs), len(latest_completed_audio_clip_tone_ids))

            #==========
            #user page, only completed
            #==========

            user_latest_completed_kwargs = []
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
                    'username': unique_user.username,
                })

            #check test setup

            self.assertEqual(len(user_latest_completed_kwargs), len(user_latest_completed_audio_clip_tone_ids))

            #==========
            #own page, latest completed, likes dislikes
            #==========

            own_latest_completed_kwargs = []
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
                        'username': unique_user.username,
                    })

            #check test setup

            self.assertEqual(len(own_latest_completed_kwargs), len(own_latest_completed_audio_clip_tone_ids))

            #start

            all_kwargs = latest_completed_kwargs + user_latest_completed_kwargs + own_latest_completed_kwargs

            for kwargs_index, current_kwargs in enumerate(all_kwargs):

                try:

                    loop_title = 'loop #' + str(kwargs_index)

                    print(loop_title)

                    #next

                    stopwatch.start()

                    request = self.client.get(
                        reverse(
                            'browse_events_api',
                            kwargs=current_kwargs
                        )
                    )

                    stopwatch.stop()

                    metrics.update({
                        loop_title + '__next__no_token': {
                            'data': current_kwargs.copy(),
                            'time_ms': stopwatch.diff_milliseconds(),
                        }
                    })

                    #check

                    self.assertEqual(request.status_code, 200)

                    #next_token, back_token, data
                    response_data = get_response_data(request)

                    self.assertEqual(len(response_data['data']), settings.EVENT_QUANTITY_PER_PAGE)

                    #[{event:event,originator:[],responder:[]}]
                    for row in response_data['data']:

                        self.assertEqual(row[''])

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

                    stopwatch.stop()

                    metrics.update({
                        loop_title + '__next_token': {
                            'data': current_kwargs.copy(),
                            'time_ms': stopwatch.diff_milliseconds(),
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

                    stopwatch.stop()

                    metrics.update({
                        loop_title + '__back_token': {
                            'data': current_kwargs.copy(),
                            'time_ms': stopwatch.diff_milliseconds(),
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

                    stopwatch.stop()

                    metrics.update({
                        loop_title + '__back_token__no_rows': {
                            'data': current_kwargs.copy(),
                            'time_ms': stopwatch.diff_milliseconds(),
                        }
                    })

                    #check

                    self.assertEqual(request.status_code, 200)

                    #next_token, back_token, data
                    response_data = get_response_data(request)

                    self.assertEqual(len(response_data['data']), 0)

                except Exception as e:

                    print(current_kwargs)
                    raise e

        #done

        self.metrics.update({inspect.currentframe().f_code.co_name: metrics})


    def test_browse_events__latest_used_audio_clip_tone(self):

        metrics = {}
        stopwatch = Stopwatch()

        for unique_user in self.unique_users:

            self.login(unique_user)

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
                    user__id=unique_user.id,
                ).order_by('-when_created', '-id')[:1]
                audio_clip_tone_id = target_row.audio_clip_tone.id
                user_latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
                user_latest_completed_kwargs.append({
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': audio_clip_role_name,
                    'next_or_back': 'next',
                    'audio_clip_tone_id': audio_clip_tone_id,
                    'username': unique_user.username,
                })
                user_latest_completed_expected_rows.append(
                    AudioClips.objects.filter(
                        audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        event__generic_status__generic_status_name='completed',
                        audio_clip_tone__id=audio_clip_tone_id,
                        user__id=unique_user.id,
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
                        user=unique_user,
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
                        'username': unique_user.username,
                        'likes_or_dislikes': likes_or_dislikes_choice,
                        'audio_clip_tone_id': audio_clip_tone_id,
                    })
                    like_dislike_rows = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                        user=unique_user,
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

                stopwatch.stop()

                metrics.update({
                    loop_title + '__next__no_token': {
                        'data': current_kwargs.copy(),
                        'time_ms': stopwatch.diff_milliseconds(),
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

                stopwatch.stop()

                metrics.update({
                    loop_title + '__next_token': {
                        'data': current_kwargs.copy(),
                        'time_ms': stopwatch.diff_milliseconds(),
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

                stopwatch.stop()

                metrics.update({
                    loop_title + '__back_token': {
                        'data': current_kwargs.copy(),
                        'time_ms': stopwatch.diff_milliseconds(),
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

                stopwatch.stop()

                metrics.update({
                    loop_title + '__back_token__no_rows': {
                        'data': current_kwargs.copy(),
                        'time_ms': stopwatch.diff_milliseconds(),
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

        metrics = {}
        stopwatch = Stopwatch()

        for unique_user in self.unique_users:

            self.login(unique_user)

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
                    user__id=unique_user.id,
                ).order_by('-when_created', '-id').last()
                audio_clip_tone_id = target_row.audio_clip_tone.id
                user_latest_completed_audio_clip_tone_ids.append(audio_clip_tone_id)
                user_latest_completed_kwargs.append({
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': audio_clip_role_name,
                    'next_or_back': 'next',
                    'audio_clip_tone_id': audio_clip_tone_id,
                    'username': unique_user.username,
                })
                user_latest_completed_expected_rows.append(
                    AudioClips.objects.filter(
                        audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        event__generic_status__generic_status_name='completed',
                        audio_clip_tone__id=audio_clip_tone_id,
                        user__id=unique_user.id,
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
                        user=unique_user,
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
                        'username': unique_user.username,
                        'likes_or_dislikes': likes_or_dislikes_choice,
                        'audio_clip_tone_id': audio_clip_tone_id,
                    })
                    like_dislike_rows = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                        user=unique_user,
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

                stopwatch.stop()

                metrics.update({
                    loop_title + 'next__no_token': {
                        'data': current_kwargs.copy(),
                        'time_ms': stopwatch.diff_milliseconds(),
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

                stopwatch.stop()

                metrics.update({
                    loop_title + 'next_token': {
                        'data': current_kwargs.copy(),
                        'time_ms': stopwatch.diff_milliseconds(),
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

                stopwatch.stop()

                metrics.update({
                    loop_title + 'back_token': {
                        'data': current_kwargs.copy(),
                        'time_ms': stopwatch.diff_milliseconds(),
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

                stopwatch.stop()

                metrics.update({
                    loop_title + 'back_token__no_rows': {
                        'data': current_kwargs.copy(),
                        'time_ms': stopwatch.diff_milliseconds(),
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

        metrics = {}
        stopwatch = Stopwatch()

        for unique_user in self.unique_users:

            self.login(unique_user)

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
                        'username': unique_user.username,
                    })
                    user_latest_completed_expected_rows.append(
                        AudioClips.objects.filter(
                            audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                            event__generic_status__generic_status_name='completed',
                            audio_clip_tone__id=audio_clip_tone_id,
                            user__id=unique_user.id,
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
                            'username': unique_user.username,
                            'likes_or_dislikes': likes_or_dislikes_choice,
                            'audio_clip_tone_id': audio_clip_tone_id,
                        })
                        like_dislike_rows = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                            user=unique_user,
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

                    stopwatch.stop()

                    metrics.update({
                        loop_title + 'next__no_token': {
                            'data': current_kwargs.copy(),
                            'time_ms': stopwatch.diff_milliseconds(),
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

                    stopwatch.stop()

                    metrics.update({
                        loop_title + 'next_token': {
                            'data': current_kwargs.copy(),
                            'time_ms': stopwatch.diff_milliseconds(),
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

                    stopwatch.stop()

                    metrics.update({
                        loop_title + 'back_token': {
                            'data': current_kwargs.copy(),
                            'time_ms': stopwatch.diff_milliseconds(),
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

                    stopwatch.stop()

                    metrics.update({
                        loop_title + 'back_token__no_rows': {
                            'data': current_kwargs.copy(),
                            'time_ms': stopwatch.diff_milliseconds(),
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

        for unique_user in self.unique_users:

            self.login(unique_user)

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
                    'username': unique_user.username,
                },
                {
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': 'responder',
                    'next_or_back': 'back',
                    'username': unique_user.username,
                },
                #has tone, completed, user
                {
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': 'originator',
                    'next_or_back': 'back',
                    'audio_clip_tone_id': audio_clip_tone.id,
                    'username': unique_user.username,
                },
                {
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': 'responder',
                    'next_or_back': 'back',
                    'audio_clip_tone_id': audio_clip_tone.id,
                    'username': unique_user.username,
                },
                #no tone, user, likes/dislikes
                {
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': 'originator',
                    'next_or_back': 'back',
                    'username': unique_user.username,
                    'likes_or_dislikes': 'likes',
                },
                {
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': 'originator',
                    'next_or_back': 'back',
                    'username': unique_user.username,
                    'likes_or_dislikes': 'dislikes',
                },
                {
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': 'responder',
                    'next_or_back': 'back',
                    'username': unique_user.username,
                    'likes_or_dislikes': 'likes',
                },
                {
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': 'responder',
                    'next_or_back': 'back',
                    'username': unique_user.username,
                    'likes_or_dislikes': 'dislikes',
                },
                #has tone, user, likes/dislikes
                {
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': 'originator',
                    'next_or_back': 'back',
                    'username': unique_user.username,
                    'likes_or_dislikes': 'likes',
                    'audio_clip_tone_id': audio_clip_tone.id,
                },
                {
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': 'originator',
                    'next_or_back': 'back',
                    'username': unique_user.username,
                    'likes_or_dislikes': 'dislikes',
                    'audio_clip_tone_id': audio_clip_tone.id,
                },
                {
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': 'responder',
                    'next_or_back': 'back',
                    'username': unique_user.username,
                    'likes_or_dislikes': 'likes',
                    'audio_clip_tone_id': audio_clip_tone.id,
                },
                {
                    'latest_or_best': 'latest',
                    'timeframe': 'all',
                    'audio_clip_role_name': 'responder',
                    'next_or_back': 'back',
                    'username': unique_user.username,
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

                stopwatch.stop()

                metrics.update({
                    'loop_'+str(index): {
                        'data': data,
                        'time_ms': stopwatch.diff_milliseconds(),
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

        metrics = {}
        stopwatch = Stopwatch()

        for unique_user in self.unique_users:

            self.login(unique_user)

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
                    user=unique_user,
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
                    'username': unique_user.username,
                })
                user_latest_completed_expected_rows.append(
                    AudioClips.objects.filter(
                        audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        event__generic_status__generic_status_name='completed',
                        user=unique_user,
                    ).order_by('-when_created', '-id')[:settings.EVENT_QUANTITY_PER_PAGE*2],
                )

            #has tone, user
            for audio_clip_role_name in ['originator', 'responder']:
                target_row = AudioClips.objects.filter(
                    audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                    event__generic_status__generic_status_name='completed',
                    user=unique_user,
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
                    'username': unique_user.username,
                })
                user_latest_completed_expected_rows.append(
                    AudioClips.objects.filter(
                        audio_clip_role__audio_clip_role_name=audio_clip_role_name,
                        audio_clip_tone__id=audio_clip_tone_id,
                        event__generic_status__generic_status_name='completed',
                        user=unique_user,
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
                        user=unique_user,
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
                        'username': unique_user.username,
                    })
                    like_dislike_rows = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                        user=unique_user,
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
                        user=unique_user,
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
                        'username': unique_user.username,
                    })
                    like_dislike_rows = AudioClipLikesDislikes.objects.select_related('audio_clip').filter(
                        user=unique_user,
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

                stopwatch.stop()

                metrics.update({
                    loop_title + 'next_token': {
                        'data': kwargs,
                        'time_ms': stopwatch.diff_milliseconds(),
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









#see RealisticBulkData._determine_unique_users_after_no_new_users_left_to_create, only expect rows from name_3
#only test for basic correctness and db test data setup
#leave API correctness at test_apis
@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    DEBUG=True,
)
class ListReplyChoices_TestCase(TestCase):

    #{test_function_name: anything}
    metrics = {}

    #create your db indexes here
    @classmethod
    def setUp(cls):

        pass


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


    def test__list_event_reply_choice(self, has_tone=False, minimum_time_elapsed_ms=180, show_test_failed_query=True, show_test_passed_query=False):

        stopwatch = Stopwatch()
        realistic_bulk_data_class = RealisticBulkData()
        unique_user_ids = realistic_bulk_data_class.get_unique_user_ids()

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
            for audio_clip_tone_index in realistic_bulk_data_class.excluded_audio_clip_tones_indexes:

                audio_clip_tone_ids['excluded'].append(
                    realistic_bulk_data_class.audio_clip_tones[audio_clip_tone_index].id
                )

                #since excluded tones are specified in earliest/middle/latest manner,
                #and will never use first and last,
                #can just -1 +1
                audio_clip_tone_ids['expected'].append(
                    realistic_bulk_data_class.audio_clip_tones[audio_clip_tone_index - 1].id
                )
                audio_clip_tone_ids['expected'].append(
                    realistic_bulk_data_class.audio_clip_tones[audio_clip_tone_index + 1].id
                )

        test_pass_count = 0
        test_fail_count = 0

        for unique_user_key in unique_user_ids:

            for unique_user_id in unique_user_ids[unique_user_key]:

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
                                    unique_user_id,
                                    unique_user_id,
                                    unique_user_id,
                                    unique_user_id,
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
                                    unique_user_id,
                                    unique_user_id,
                                    unique_user_id,
                                    unique_user_id,
                                ]
                            )

                        earliest_event = earliest_event[0]
                        latest_event = latest_event[0]

                        minimum_datetimes.append(earliest_event.when_created)
                        minimum_datetimes.append(latest_event.when_created)

                        for minimum_datetime_index, minimum_datetime in enumerate(minimum_datetimes):

                            result = None

                            if has_tone is True:

                                result = self._query_1(
                                    current_user_id=unique_user_id,
                                    audio_clip_tone_id=audio_clip_tone_id,
                                    when_created=minimum_datetime,
                                )

                            else:

                                result = self._query_0(
                                    current_user_id=unique_user_id,
                                    when_created=minimum_datetime,
                                )

                            #name_3 will always have row
                            #we want to do "_3" so we don't let "33" pass
                            current_user = get_user_model().objects.get(pk=unique_user_id)
                            current_user_group = current_user.username[len(current_user.username)-2 : len(current_user.username)]

                            #check

                            is_row_count_ok = False

                            if len(result['query_result']) == 1:

                                #will always have 1 row, and row belonging to _3 username group
                                #provided that user_blocks are created correctly,
                                #and _3 users have proper incomplete events that fulfill reply choice criteria

                                fetched_user = result['query_result'][0].user
                                fetched_user_group = fetched_user.username[len(fetched_user.username)-2 : len(fetched_user.username)]

                                if current_user_group == '_3' or fetched_user_group == '_3':

                                    is_row_count_ok = True

                            #specify minimum_time_elapsed_ms to hide/show benchmark that matters
                            if is_row_count_ok is True and result['time_elapsed_ms'] < minimum_time_elapsed_ms:
                            
                                print('\n')

                                if show_test_passed_query is True:
                                
                                    print(result['raw_query'])

                                print('Good')
                                print({
                                    'unique_user_username': current_user.username,
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
                                'unique_user_username': current_user.username,
                                'earliest_or_latest_datetime': 'earliest' if minimum_datetime_index == 0 else 'latest',
                                'minimum_datetime': minimum_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                                'time_elapsed_ms': result['time_elapsed_ms'],
                            })
                            print('\n')

                            test_fail_count += 1

        print({
            'tests_passed': test_pass_count,
            'tests_failed': test_fail_count,
        })


    def test__has_tone(self, minimum_time_elapsed_ms=200, show_test_failed_query=False,):

        stopwatch = Stopwatch()
        unique_user_ids = RealisticBulkData.get_unique_user_ids()

        excluded_audio_clip_tone_ids = []
        expected_audio_clip_tone_ids = []

        realistic_bulk_data_class = RealisticBulkData()

        #add excluded audio_clip_tones
        for audio_clip_tone_index in realistic_bulk_data_class.excluded_audio_clip_tones_indexes:

            excluded_audio_clip_tone_ids.append(
                realistic_bulk_data_class.audio_clip_tones[audio_clip_tone_index].id
            )

            #since excluded tones are specified in earliest/middle/latest manner,
            #and will never use first and last,
            #can just -1 +1
            expected_audio_clip_tone_ids.append(
                realistic_bulk_data_class.audio_clip_tones[audio_clip_tone_index - 1].id
            )
            expected_audio_clip_tone_ids.append(
                realistic_bulk_data_class.audio_clip_tones[audio_clip_tone_index + 1].id
            )

        test_pass_count = 0
        test_fail_count = 0

        for unique_user_key in unique_user_ids:

            for unique_user in unique_user_ids[unique_user_key]:

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
                            current_user_id=unique_user.id,
                            audio_clip_tone_id=audio_clip_tone_id,
                            when_created=minimum_datetime,
                        )

                        is_row_count_expected = len(result['query_result']) > 0

                        if is_row_count_expected is True and result['time_elapsed_ms'] < minimum_time_elapsed_ms:

                            print('Good')
                            print({
                                'audio_clip_tone_id': audio_clip_tone_id,
                                'unique_user_username': unique_user.username,
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
                            'unique_user_username': unique_user.username,
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
                        current_user_id=unique_user.id,
                        audio_clip_tone_id=audio_clip_tone_id,
                        when_created=minimum_datetime,
                    )

                    is_row_count_expected = len(result['query_result']) == 0

                    if is_row_count_expected is True and result['time_elapsed_ms'] < minimum_time_elapsed_ms:

                        print('Good')
                        print({
                            'audio_clip_tone_id': audio_clip_tone_id,
                            'unique_user_username': unique_user.username,
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
                        'unique_user_username': unique_user.username,
                        'minimum_datetime': minimum_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                        'time_elapsed_ms': result['time_elapsed_ms'],
                    })
                    print('\n')

                    test_fail_count += 1

        print({
            'tests_passed': test_pass_count,
            'tests_failed': test_fail_count,
        })





















#see RealisticBulkData._determine_unique_users_after_no_new_users_left_to_create, only expect rows from name_3
#only test for basic correctness and db test data setup
#leave API correctness at test_apis
@override_settings(
    DEBUG_TOOLBAR_CONFIG={'SHOW_TOOLBAR_CALLBACK': lambda r: False},
    DEBUG=True,
)
class OptimiseBrowseEvents_TestCase(TestCase):

    #{test_function_name: anything}
    metrics = {}

    #create your db indexes here
    @classmethod
    def setUp(cls):

        pass










































