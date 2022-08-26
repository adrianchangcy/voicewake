#this is where you write unit testing as per Django's ways
#proper ways coming soon
#Django
from django.test import TestCase

#apps
from .services import *
from .models import *

#py packages
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


#note that every function is a form submit, hence recreating instances
class TalkerListenerActionsTestCase(TestCase):

    #setUp() is run once before every test case
    #there are other functions to look into too, but this is currently not important
    def setUp(self):
        
        #to-do: fix 'relation does not exist' error

        self.talker_user = AuthUser.objects.create(
            username='adrian',
            password='123',
            is_superuser=True,
            is_staff=False,
            is_active=True,
            email='adrianchangcy@gmail.com',
            date_joined=datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S').astimezone(ZoneInfo('UTC')),
        )
        self.listener_user = AuthUser.objects.create(
            username='yoyo',
            password='123',
            is_superuser=False,
            is_staff=False,
            is_active=True,
            email='adrianchangcy@gmail.com',
            date_joined=datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S').astimezone(ZoneInfo('UTC')),
        )

        talker_role = EventRoles.objects.create(event_role_name='talker')
        listener_role = EventRoles.objects.create(event_role_name='listener')

        UserEventRoles.objects.create(user=self.talker_user, event_role=talker_role)
        UserEventRoles.objects.create(user=self.listener_user, event_role=listener_role)

        Languages.objects.create(language_name='English')

        #create this because this will not be free-for-all
        EventPurposes.objects.create(event_purpose_name='motivation')

        #event_statuses
        #using "" because of drag-and-drop directly from db
        EventStatuses.objects.bulk_create([
            EventStatuses(event_status_name="available"),
            EventStatuses(event_status_name="fulfilled"),
            EventStatuses(event_status_name="overdue"),
            EventStatuses(event_status_name="waiting_for_mp3_conversion"),
            EventStatuses(event_status_name="file_ready"),
            EventStatuses(event_status_name="file_error"),
            EventStatuses(event_status_name="request_pending"),
            EventStatuses(event_status_name="request_accepted"),
            EventStatuses(event_status_name="request_fulfilled"),
            EventStatuses(event_status_name="request_rejected"),
        ])

        #event_request_statuses
        EventRequestStatuses.objects.bulk_create([
            EventRequestStatuses(event_request_status_name="request_pending"),
            EventRequestStatuses(event_request_status_name="request_accepted"),
            EventRequestStatuses(event_request_status_name="request_fulfilled"),
            EventRequestStatuses(event_request_status_name="request_rejected"),
        ])

        #fixed preferences, assuming identical between listener and talker
        self.event_purpose_submit = 'motivation'
        self.event_tone_submit = 'Megatron'

        self.listener_creates_event()


    def listener_creates_event(self):

        listener_actions = ListenerActions()

        self.assertTrue(listener_actions.set_user_and_listener(request_user_id=self.listener_user.id))

        listener_actions.set_event_preferences(
            event_purpose_name='motivation',
            event_tone_name='Megatron'
        )

        listener_actions.create_event(
            form_datetime = datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S').astimezone(tz=ZoneInfo('UTC')),
            form_event_name = 'Trip to Mordor',
            form_event_message = 'Excited! :)'
        )


    def test_talker_finds_listener(self):
        
        talker_actions = TalkerActions()

        self.assertTrue(talker_actions.set_user_and_talker(request_user_id=self.talker_user.id))

        self.assertTrue(
            talker_actions.set_event_preferences(
                event_purpose_name=self.event_purpose_submit,
                event_tone_name=self.event_tone_submit
            )
        )

        talker_actions.seek_listener_events()



