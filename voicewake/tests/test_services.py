#this is where you write unit testing as per Django's ways
#proper ways coming soon
#Django
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

#apps
from voicewake.services import *
from voicewake.models import *

#py packages
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


class User_SignUp_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.username = 'listener_here'
        cls.email = 'abc@gmail.com'
        cls.password = 'tarantula123'

        Languages.objects.create(language_name='English')

        Countries.objects.create(country_name='United States of America')

        EventRoles.objects.bulk_create([
            EventRoles(event_role_name='talker'),
            EventRoles(event_role_name='listener'),
        ])

    def test_sign_up_via_post(self):

        #reverse() requires url 'name' arg as part of DRY principle
        response = self.client.post(reverse('sign_up'), data={
            'username': self.username,
            'email': self.email,
            'password1': self.password,
            'password2': self.password
        })

        #get all users
        users = AuthUser.objects.all()

        #check for creation success, redirect to home, and 1 total AuthUser obj
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/')
        self.assertTrue(len(users) == 1)

        #get all event roles
        user_event_roles = UserEventRoles.objects.select_related().all()

        #check for 2 user event roles created by AppConfig
        self.assertTrue(len(user_event_roles) == 2)

        #check for correct 2 user event roles created by AppConfig
        to_expect = ['talker', 'listener']

        for uer in user_event_roles:

            #check for precise event roles
            event_role_name = uer.event_role.event_role_name

            if event_role_name in to_expect:

                to_expect.pop(to_expect.index(event_role_name))

            else:

                raise ValueError('Existing event_role_name is unexpected, as dictated by "to_expect" list.')
        
        #check for user's given_score for talker or null for listener, as created by AppConfig
        for uer in user_event_roles:

            if uer.event_role.event_role_name == 'talker':

                if uer.given_scores == [0,0,0,0,0]:

                    pass

                else:

                    raise ValueError('Expected [0,0,0,0,0] for given_score of talker, but did not get it.')

            elif uer.event_role.event_role_name == 'listener':

                if uer.given_scores is None:

                    pass

                else:

                    raise ValueError('Expected null for given_score of listener, but got something else.')


#note that for ListenerActions() and TalkerActions(),
#we test in isolated steps, with each step possibly repeating previous steps' code
#gets more and more complex

#ListenerActions() 1, basics
#set_user_and_listener(), set_event_preferences()
#dependencies:
    #User_SignUp_TestCase
class ListenerActions_Basics_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        Languages.objects.create(language_name='English')

        Countries.objects.create(country_name='United States of America')

        EventPurposes.objects.bulk_create([
            EventPurposes(event_purpose_name='motivation')
        ])


    def test_set_user_and_listener(self):

        #create user
        self.client.post(reverse('sign_up'), data={
            'username': 'listener_here',
            'email': 'abc@gmail.com',
            'password1': 'tarantula123',
            'password2': 'tarantula123'
        })

        #get user
        user = AuthUser.objects.all().first()

        #start testing ListenerActions()
        listener_actions = ListenerActions()

        self.assertTrue(listener_actions.set_user_and_listener(request_user_id=user.id))

        #check if it has retrieved listener UserEventRole for us
        listener = getattr(listener_actions, 'listener')
        self.assertTrue(isinstance(listener, UserEventRoles))
        self.assertTrue(listener.event_role.event_role_name == 'listener')

    
    def test_set_event_preferences(self):

        #create user
        self.client.post(reverse('sign_up'), data={
            'username': 'listener_here',
            'email': 'abc@gmail.com',
            'password1': 'tarantula123',
            'password2': 'tarantula123'
        })

        #get user
        user = AuthUser.objects.all().first()

        #start testing ListenerActions()
        listener_actions = ListenerActions()

        listener_actions.set_user_and_listener(request_user_id=user.id)

        #expect False on required event_purpose_name
        self.assertFalse(
            listener_actions.set_event_preferences(
                event_purpose_name='',
                language_name='English',
                event_tone_name=''
            )
        )

        #expect False on required language_name
        self.assertFalse(
            listener_actions.set_event_preferences(
                event_purpose_name='motivation',
                language_name='',
                event_tone_name=''
            )
        )

        #set preferences, will be True as event_tone_name is optional
        self.assertTrue(
            listener_actions.set_event_preferences(
                event_purpose_name='motivation',
                language_name='English',
                event_tone_name=''
            )
        )

        #check if preferences are properly set
        self.assertTrue(isinstance(getattr(listener_actions, 'form_event_purpose'), EventPurposes))
        self.assertTrue(isinstance(getattr(listener_actions, 'form_language'), Languages))
        self.assertEqual(getattr(listener_actions, 'form_event_tone'), None)

        #set preferences with all fields
        self.assertTrue(
            listener_actions.set_event_preferences(
                event_purpose_name='motivation',
                language_name='English',
                event_tone_name='Megatron'
            )
        )
        
        #check if preferences are properly set
        self.assertTrue(isinstance(getattr(listener_actions, 'form_event_purpose'), EventPurposes))
        self.assertTrue(isinstance(getattr(listener_actions, 'form_language'), Languages))
        self.assertTrue(isinstance(getattr(listener_actions, 'form_event_tone'), EventTones))



#ListenerActions() 2, create event with no specific talker
#create_event()
#dependencies:
    #UserSignUp_TestCase
    #ListenerActions_Basics_TestCase
class ListenerActions_CreateEvent_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        Languages.objects.create(language_name='English')

        Countries.objects.create(country_name='United States of America')

        EventStatuses.objects.bulk_create([
            EventStatuses(event_status_name='available')
        ])

        EventPurposes.objects.bulk_create([
            EventPurposes(event_purpose_name='motivation')
        ])

        cls.form_when_trigger = datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S').astimezone(tz=ZoneInfo('UTC'))
        cls.form_event_name = "Couldn't qualify for PTPTN"
        cls.form_event_message = 'Feeling sad! :('


    def test_create_listener_events(self):

        #create user
        self.client.post(reverse('sign_up'), data={
            'username': 'listener_here',
            'email': 'abc@gmail.com',
            'password1': 'tarantula123',
            'password2': 'tarantula123'
        })

        #get user
        user = AuthUser.objects.all().first()

        #start testing ListenerActions()
        listener_actions = ListenerActions()

        listener_actions.set_user_and_listener(request_user_id=user.id)

        #set preferences
        listener_actions.set_event_preferences(
            event_purpose_name='motivation',
            language_name='English',
            event_tone_name=''
        )

        #expect False on required when_trigger
        self.assertRaises(
            ValueError,
            listener_actions.create_event,
            form_when_trigger='',
            form_event_name='',
            form_event_message='',
            with_request=False,
            talker_user_id=None
        )
        #expect False on no timezone
        self.assertRaises(
            ValueError,
            listener_actions.create_event,
            form_when_trigger=datetime.now(),
            form_event_name='',
            form_event_message='',
            with_request=False,
            talker_user_id=None
        )
        #expect False on no event_name
        self.assertRaises(
            ValueError,
            listener_actions.create_event,
            form_when_trigger=self.form_when_trigger,
            form_event_name='',
            form_event_message='',
            with_request=False,
            talker_user_id=None
        )

        #create event
        self.assertTrue(
            listener_actions.create_event(
                form_when_trigger=self.form_when_trigger,
                form_event_name=self.form_event_name,
                form_event_message=self.form_event_message,
                with_request=False,
                talker_user_id=None
            )
        )

        #check for created event
        self.assertTrue(Events.objects.count() == 1)

        #check for event properties
        event = Events.objects.all().first()
        self.assertEqual(event.user_event_role, getattr(listener_actions, 'listener'))
        self.assertEqual(event.event_purpose, getattr(listener_actions, 'form_event_purpose'))
        self.assertEqual(event.language, getattr(listener_actions, 'form_language'))
        self.assertEqual(event.event_tone, getattr(listener_actions, 'form_event_tone'))
        self.assertEqual(event.event_status.event_status_name, 'available')
        self.assertEqual(event.when_trigger, self.form_when_trigger)
        self.assertEqual(event.event_name, self.form_event_name)
        self.assertEqual(event.event_message, self.form_event_message)
        self.assertEqual(event.audio_file, '')
        self.assertEqual(len(EventRequests.objects.all()), 0)
        self.assertEqual(len(EventRooms.objects.all()), 0)
        self.assertEqual(len(EventRoomMatches.objects.all()), 0)



#ListenerActions() 3, create event that requests a specific talker
#create_event()
#dependencies:
    #UserSignUp_TestCase
    #ListenerActions_Basics_TestCase
    #ListenerActions_CreateEvent_TestCase
class ListenerActions_CreateEventWithRequest_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        Languages.objects.create(language_name='English')

        Countries.objects.create(country_name='United States of America')

        EventStatuses.objects.bulk_create([
            EventStatuses(event_status_name='available'),
            EventStatuses(event_status_name='request_pending'),
        ])

        EventRequestStatuses.objects.bulk_create([
            EventRequestStatuses(event_request_status_name='request_pending'),
        ])

        EventPurposes.objects.bulk_create([
            EventPurposes(event_purpose_name='motivation')
        ])

        cls.form_when_trigger = datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S').astimezone(tz=ZoneInfo('UTC'))
        cls.form_event_name = 'Important meeting'
        cls.form_event_message = 'Help pls ty'


    def test_listener_creates_event_request_to_talker(self):
        
        #create listener user
        self.client.post(reverse('sign_up'), data={
            'username': 'listener_here',
            'email': 'abc@gmail.com',
            'password1': 'tarantula123',
            'password2': 'tarantula123'
        })
        #create talker user
        self.client.post(reverse('sign_up'), data={
            'username': 'talker_here',
            'email': 'abc@gmail.com',
            'password1': 'tarantula123',
            'password2': 'tarantula123'
        })

        #init listener
        listener_actions = ListenerActions()

        listener_actions.set_user_and_listener(
            request_user_id = AuthUser.objects.get(username='listener_here').id
        )

        #set listener preferences
        listener_actions.set_event_preferences(
            event_purpose_name = 'motivation',
            language_name = 'English',
            event_tone_name = ''
        )

        #listener creates event request to talker
        self.assertTrue(            
            listener_actions.create_event(
                form_when_trigger = self.form_when_trigger,
                form_event_name = self.form_event_name,
                form_event_message = self.form_event_message,
                with_request = True,
                talker_user_id = AuthUser.objects.get(username='talker_here').id,
            )
        )

        #check that records have been created
        self.assertTrue(Events.objects.count() == 1)
        self.assertTrue(EventRequests.objects.count() == 1)

        #check for no accidental records created
        self.assertTrue(EventRooms.objects.count() == 0)
        self.assertTrue(EventRoomMatches.objects.count() == 0)

        #evaluate Events object
        event = Events.objects.all().first()
        self.assertEqual(event.user_event_role, getattr(listener_actions, 'listener'))
        self.assertEqual(event.event_purpose, getattr(listener_actions, 'form_event_purpose'))
        self.assertEqual(event.language, getattr(listener_actions, 'form_language'))
        self.assertEqual(event.event_tone, getattr(listener_actions, 'form_event_tone'))
        self.assertEqual(event.event_status.event_status_name, 'request_pending')
        self.assertEqual(event.when_trigger, self.form_when_trigger)
        self.assertEqual(event.event_name, self.form_event_name)
        self.assertEqual(event.event_message, self.form_event_message)
        self.assertEqual(event.audio_file, '')

        #evaluate EventRequests object
        event_request = EventRequests.objects.all().first()
        self.assertEqual(
            event_request.user_event_role,
            UserEventRoles.objects.get(user__username='listener_here', event_role__event_role_name='listener')
        )
        self.assertEqual(
            event_request.requested_user_event_role,
            UserEventRoles.objects.get(user__username='talker_here', event_role__event_role_name='talker')
        )
        self.assertEqual(event_request.event, event)
        self.assertEqual(event_request.event_request_status.event_request_status_name, 'request_pending')
        self.assertEqual(event_request.payment_id, None)


    def test_listener_creates_event_request_with_payment(self):
        pass



#TalkerActions() 1, basics
#set_user_and_talker(), set_event_preferences()
#dependencies:
    #User_SignUp_TestCase
    #ListenerActions_CreateEvent_TestCase
class TalkerActions_Basics_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        Languages.objects.create(language_name='English')

        Countries.objects.create(country_name='United States of America')

        EventStatuses.objects.bulk_create([
            EventStatuses(event_status_name='available')
        ])

        EventPurposes.objects.bulk_create([
            EventPurposes(event_purpose_name='motivation')
        ])


    def test_set_user_and_talker(self):

        #create user
        self.client.post(reverse('sign_up'), data={
            'username': 'talker_here',
            'email': 'abc@gmail.com',
            'password1': 'tarantula123',
            'password2': 'tarantula123'
        })

        #get user
        user = AuthUser.objects.all().first()

        #start testing TalkerActions()
        talker_actions = TalkerActions()

        self.assertTrue(talker_actions.set_user_and_talker(request_user_id=user.id))

        #check if it has retrieved listener UserEventRole for us
        talker = getattr(talker_actions, 'talker')
        self.assertTrue(isinstance(talker, UserEventRoles))
        self.assertTrue(talker.event_role.event_role_name == 'talker')

    
    def test_set_event_preferences(self):

        #create user
        self.client.post(reverse('sign_up'), data={
            'username': 'talker_here',
            'email': 'abc@gmail.com',
            'password1': 'tarantula123',
            'password2': 'tarantula123'
        })

        #get user
        user = AuthUser.objects.all().first()

        #start testing TalkerActions()
        talker_actions = TalkerActions()

        talker_actions.set_user_and_talker(request_user_id=user.id)

        #expect False on required event_purpose_name
        self.assertFalse(
            talker_actions.set_event_preferences(
                event_purpose_name='',
                language_name='English',
                event_tone_name=''
            )
        )

        #expect False on required language_name
        self.assertFalse(
            talker_actions.set_event_preferences(
                event_purpose_name='motivation',
                language_name='',
                event_tone_name=''
            )
        )

        #set preferences, will be True as event_tone_name is optional
        self.assertTrue(
            talker_actions.set_event_preferences(
                event_purpose_name='motivation',
                language_name='English',
                event_tone_name=''
            )
        )

        #check if preferences are properly set
        self.assertTrue(isinstance(getattr(talker_actions, 'form_event_purpose'), EventPurposes))
        self.assertTrue(isinstance(getattr(talker_actions, 'form_language'), Languages))
        self.assertEqual(getattr(talker_actions, 'form_event_tone'), None)

        #set preferences with all fields
        self.assertTrue(
            talker_actions.set_event_preferences(
                event_purpose_name='motivation',
                language_name='English',
                event_tone_name='Megatron'
            )
        )
        
        #check if preferences are properly set
        self.assertTrue(isinstance(getattr(talker_actions, 'form_event_purpose'), EventPurposes))
        self.assertTrue(isinstance(getattr(talker_actions, 'form_language'), Languages))
        self.assertTrue(isinstance(getattr(talker_actions, 'form_event_tone'), EventTones))


#TalkerActions() 2, seek listener events
#seek_listener_events()
#dependencies:
    #ListenerActions_CreateEvent_TestCase
    #ListenerActions_CreateEventWithRequest_TestCase
    #TalkerActions_Basics_TestCase
class TalkerActions_SeekEvents_TestCase(TestCase):

    @classmethod
    def setUpTestData(cls):

        Languages.objects.bulk_create([
            Languages(language_name='English', language_name_shortened='ENG'),
            Languages(language_name='Japanese', language_name_shortened='JPY'),
        ])

        Countries.objects.bulk_create([
            Countries(country_name='United States of America'),
            Countries(country_name='Japan'),
        ])

        EventStatuses.objects.bulk_create([
            EventStatuses(event_status_name='available'),
            EventStatuses(event_status_name='locked_for_talker_choice'),
        ])

        EventPurposes.objects.bulk_create([
            EventPurposes(event_purpose_name='motivation'),
            EventPurposes(event_purpose_name='insult'),
        ])

        cls.datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))


    def test_seek_events(self):

        #create user and use it as listener
        self.client.post(reverse('sign_up'), data={
            'username': 'listener_here',
            'email': 'abc@gmail.com',
            'password1': 'tarantula123',
            'password2': 'tarantula123'
        })

        user = AuthUser.objects.get(username='listener_here')

        #init listener
        listener_actions = ListenerActions()
        listener_actions.set_user_and_listener(request_user_id=user.id)

        #set preferences on submit to create listener event 1
        listener_actions.set_event_preferences(
            event_purpose_name='motivation',
            language_name='English',
            event_tone_name=''
        )

        #create listener event 1
        listener_actions.create_event(
            form_when_trigger=self.datetime_now,
            form_event_name='aaa',
            form_event_message='',
            with_request=False,
            talker_user_id=None
        )

        #set preferences on submit to create listener event 2
        listener_actions.set_event_preferences(
            event_purpose_name='motivation',
            language_name='Japanese',
            event_tone_name='Megatron'
        )

        #create listener event 2
        listener_actions.create_event(
            form_when_trigger=self.datetime_now,
            form_event_name='bbb',
            form_event_message='',
            with_request=False,
            talker_user_id=None
        )

        #set preferences on submit to create listener event 3
        listener_actions.set_event_preferences(
            event_purpose_name='insult',
            language_name='Japanese',
            event_tone_name=''
        )

        #create listener event 3
        listener_actions.create_event(
            form_when_trigger=self.datetime_now,
            form_event_name='bbb',
            form_event_message='',
            with_request=False,
            talker_user_id=None
        )

        #create user and use it as talker
        self.client.post(reverse('sign_up'), data={
            'username': 'talker_here',
            'email': 'abc@gmail.com',
            'password1': 'tarantula123',
            'password2': 'tarantula123'
        })

        user = AuthUser.objects.get(username='talker_here')

        #init talker
        talker_actions = TalkerActions()
        talker_actions.set_user_and_talker(request_user_id=user.id)

        #set preferences on submit
        talker_actions.set_event_preferences(
            event_purpose_name='motivation',
            language_name='English',
            event_tone_name=''
        )

        #get found listener events
        print(len(talker_actions.seek_listener_events()))





