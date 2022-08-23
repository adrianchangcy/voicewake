#this is where you write unit testing as per Django's ways
#proper ways coming soon
#Django
from django.test import TestCase

from .services import *
from .models import *

#note that every function is a form submit, hence recreating instances
class TalkerListenerActionsTestCase(TestCase):

    def setUp(self):
        
        #to-do: find out how to run on db copy instead of blank db
        self.talker_user = AuthUser.objects.create(
            username='adrian',
            password='123',
            is_superuser=True,
            is_staff=False,
            is_active=True,
            email='adrianchangcy@gmail.com',
            date_joined=datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S'),
        )
        self.listener_user = AuthUser.objects.create(
            username='yoyo',
            password='123',
            is_superuser=False,
            is_staff=False,
            is_active=True,
            email='adrianchangcy@gmail.com',
            date_joined=datetime.strptime('2022-01-01 00:00:00', '%Y-%m-%d %H:%M:%S'),
        )

        talker_role = EventRoles.objects.create(event_role_name='talker')
        listener_role = EventRoles.objects.create(event_role_name='listener')

        UserEventRoles.objects.create(user=self.talker_user, event_role=talker_role)
        UserEventRoles.objects.create(user=self.listener_user, event_role=listener_role)

        Languages.objects.create(language_name='English', is_legitimate=True)

        self.event_purpose_submit = 'motivation'
        self.language_submit = 'English'
        self.event_tone_submit = 'Megatron'


    def listener_creates_event(self):

        listener_actions = ListenerActions()

        self.assertTrue(listener_actions.set_user_and_listener(request_user=self.listener_user.id))

        listener_actions.set_event_preferences(event_purpose='motivation', language='English', event_tone='Megatron')

        listener_actions.create_event(
            form_date = datetime.strptime('2022-01-01'),
            form_time = datetime.strptime('01:00:00'),
            form_event_name = 'Trip to Mordor',
            form_event_message = 'Excited! :)'
        )


    def test_talker_finds_listener(self):
        
        talker_actions = TalkerActions()

        self.assertTrue(talker_actions.set_user_and_talker(request_user=self.talker_user.id))

        self.assertTrue(talker_actions.set_event_preferences(event_purpose='motivation', language='English', event_tone='Megatron'))

        talker_actions.seek_listener_events()



