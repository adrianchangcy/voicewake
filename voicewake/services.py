#here, we define business logic

#Django libraries
from django.db.models import Q, Case, When, Value
from django.db import connection
from django.core.files.base import File

#Python libraries
from datetime import datetime, timezone, timedelta, tzinfo
from genericpath import isfile
from zoneinfo import ZoneInfo
from pydub import AudioSegment
import os

#app files
from .models import *
from .serializers import *
from .settings import MEDIA_ROOT

#miscellaneous
from .static.values.values import LISTENER_EVENT_SEARCH_LIMIT, TALKER_EVENT_CHOICE_MAX_DURATION_SECONDS


#check Model.FileField object for malicious code
def validate_audio_file(file):
    pass


#run this to catch those 'locked_for_talker_choice' rows that were not reverted properly
#e.g. user exits website
def unlock_overdue_listener_events(
    minimum_seconds_passed=TALKER_EVENT_CHOICE_MAX_DURATION_SECONDS,
    max_rows=200
):

    #add precautionary extra seconds
    minimum_seconds_passed += 10

    datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC')) - timedelta(seconds=minimum_seconds_passed)

    events = Events.objects.filter(
        user_event_role__event_role__event_role_name = 'listener',
        event_status__event_status_name = 'locked_for_talker_choice',
        when_locked__lt = datetime_now
    ).order_by(
        'when_locked'
    )[:max_rows]

    #has events, update their event_status to 'available'
    for event in events:

        event.event_status = EventStatuses.objects.get(event_status_name='available')
        event.when_locked = None

    Events.objects.bulk_update(events, ['event_status', 'when_locked'])

    return True



#call this function as REST API via a standalone script, then run that script via cronjob
#we currently rely on ffmpeg conversion to check for file integrity
def convert_event_audio_files_to_mp3():

    #find files to convert to mp3
    events = Events.objects.filter(
        Q(audio_file__isnull=False) &
        Q(event_status__event_status_name='waiting_for_mp3_conversion')
    ).order_by('when_created')[:10]
    
    if len(events) == 0:
        
        #nothing to process
        return

    old_files_to_delete = []

    for event in events:

        source = event.audio_file.path
        split_name_and_extension = source.rsplit('.', 1)
        extension = split_name_and_extension[-1]

        #queue "old" non-mp3 files for deletion
        #no need to delete "old" non-mp3 files because ffmpeg will replace for us
        if extension != 'mp3':

            old_files_to_delete.append(source)

        try:

            #make mp3 the default, as aac needs further configurations
            #new files from export() will replace themselves
            sound = AudioSegment.from_file(source, format=extension)
            new_source = split_name_and_extension[0] + '.' + 'mp3'
            sound.export(new_source, format='mp3', bitrate='192k')

            #assign new file to Events object
            with open(new_source) as f:
                
                new_name = (event.audio_file.name).rsplit('.', 1)[0] + '.' + 'mp3'
                event.audio_file = File(f, name=new_name)
                event.event_status = EventStatuses.objects.get_or_create(event_status_name='file_ready')[0]

                f.close()

        except:

            #handle faulty file
            event.audio_file = None
            event.event_status = EventStatuses.objects.get_or_create(event_status_name='file_error')[0]

            continue

    Events.objects.bulk_update(events, ['event_status', 'audio_file'])

    for old_file in old_files_to_delete:

        if os.path.isfile(old_file):

            os.remove(old_file)

    print(connection.queries)
    return True





    

    







class TalkerActions():

    #when modifying this to handle 1-many, store records in []
    def __init__(
        self, user=None,
        form_event_purpose=None, form_language=None, form_event_tone=None,
        talker=None, talker_event=None, event_request=None,
        listener=None, listener_event=None,
        event_room=None, talker_event_room_match=None, listener_event_room_match=None,
    ):

        #talker and listener are UserEventRoles instances
        self.user = user

        #these event preferences are only from form submit
        #passing form directly makes it harder to test
        self.form_event_purpose = form_event_purpose
        self.form_language = form_language
        self.form_event_tone = form_event_tone

        self.talker = talker
        self.talker_event = talker_event
        self.event_request = event_request

        self.listener = listener
        self.listener_event = listener_event

        self.event_request = event_room
        self.talker_event_room_match = talker_event_room_match
        self.listener_event_room_match = listener_event_room_match


    def set_user_and_talker(self, request_user_id):

        self.user = AuthUser.objects.get(pk=request_user_id)

        self.talker = UserEventRoles.objects.get(
            user=self.user,
            event_role__event_role_name='talker'
        )

        return True


    #pre-queries model instances based on form submit for coding convenience
        #only event_tone is optional
    #accept and set as pure strings, as model objects are not necessary
    #currently has no regex
    def set_event_preferences(self, event_purpose_name, language_name, event_tone_name=''):

        #currently does not handle 'a', 'a   ', '', '   ', 'English' and 'english', etc.
        #when None, it implicitly means 'any', a.k.a. this column doesn't matter in QuerySet

        if event_purpose_name and language_name:

            self.form_event_purpose = EventPurposes.objects.get(event_purpose_name=event_purpose_name)
            self.form_language = Languages.objects.get(language_name=language_name)

        else:

            return False

        #self.form_event_tone is already None by default
        if event_tone_name:

            self.form_event_tone = EventTones.objects.get_or_create(event_tone_name=event_tone_name)[0]

        return True


    def seek_listener_events(self, max_listeners_to_find=LISTENER_EVENT_SEARCH_LIMIT):

        #query
        events = Events.objects.filter(
            user_event_role__event_role__event_role_name = 'listener',
            event_status__event_status_name = 'available',
            event_purpose__event_purpose_name = self.form_event_purpose,
            language__language_name = self.form_language,
        ).order_by(
            'when_trigger'
        )[:max_listeners_to_find]

        #has events, update their event_status to 'locked_for_talker_choice'
        if len(events) > 0:

            datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))

            for event in events:

                event.event_status = EventStatuses.objects.get(event_status_name='locked_for_talker_choice')
                event.when_locked = datetime_now

            Events.objects.bulk_update(events, ['event_status', 'when_locked'])

        return events


    #pass a list of event id to unlock,
    #of which are listener events presented as choices just moments ago that were not chosen
    #can pass no id for easy use of function
    def unlock_not_chosen_listener_events(self, all_event_id=[]):

        if isinstance(all_event_id, list) and len(all_event_id) > 0:

            events = Events.objects.filter(pk__in=all_event_id)

            for event in events:

                event.event_status = EventStatuses.objects.get(event_status_name='available')
                event.when_locked = None

            events.save()
        
        return True


    def create_talker_listener_match(self):

        #expect the listener event selected by talker to exist
        if self.listener_event is None:

            return False

        #create talker event
        #when_trigger will create timezone-aware datetime object as default
        self.talker_event = Events.objects.create(
            user_event_role=self.talker,
            language=Languages.objects.get(language_name=self.form_language),
            event_purpose=EventPurposes.objects.get(event_purpose_name=self.form_event_purpose),
            event_tone=EventTones.objects.get(event_tone_name=self.form_event_tone),
            event_status=EventStatuses.objects.get(event_status_name='talking_recording'),
            audio_file=None
        )

        #update listener status
        self.listener_event.event_status = EventStatuses.objects.get(event_status_name='has_match')
        self.listener_event.save()

        #create event_room
        self.event_room = EventRooms.objects.create()

        #create event_room_matches for talker event
        EventRoomMatches.objects.create(
            event=self.talker_event,
            event_room=self.event_room
        )

        #create event_room_matches for listener event
        EventRoomMatches.objects.create(
            event=self.listener_event,
            event_room=self.event_room
        )

        return True


    def end_match_as_talker(self, audio_file):

        #save file
        self.talker_event.audio_file = audio_file
        self.talker_event.event_status = EventStatuses.objects.get(event_status_name='waiting_for_mp3_conversion')
        self.talker_event.save()

        datetime_now = datetime.now(tz=ZoneInfo('UTC'))

        #update when_left at event_room_matches
        self.talker_event_room_match = EventRoomMatches.objects.get(event=self.talker_event)
        self.talker_event_room_match.when_left = datetime_now
        self.talker_event_room_match.save()

        return True



class ListenerActions():

    #when modifying this to handle 1-many, store records in []
    def __init__(
        self, user=None,
        form_event_purpose=None, form_language=None, form_event_tone=None,
        listener=None, listener_event=None, listener_event_room_match=None,
        talker=None, talker_event=None,
        event_request=None
    ):

        #talker and listener are UserEventRoles instances
        #form param is to get event specifications from form submit
        self.user = user

        #these event preferences are only from form submit
        #passing form directly makes it harder to test
        self.form_event_purpose = form_event_purpose
        self.form_language = form_language
        self.form_event_tone = form_event_tone

        self.listener = listener
        self.listener_event = listener_event
        self.listener_event_room_match = listener_event_room_match

        self.talker = talker
        self.talker_event = talker_event
        self.event_request = event_request


    def set_user_and_listener(self, request_user_id):

        self.user = AuthUser.objects.get(pk=request_user_id)

        self.listener = UserEventRoles.objects.get(
            user=self.user,
            event_role__event_role_name='listener'
        )

        return True


    #pre-queries model instances based on form submit for coding convenience
        #only event_tone is optional
    def set_event_preferences(self, event_purpose_name, language_name, event_tone_name=''):

        #currently does not handle 'a', 'a   ', '', '   ', 'English' and 'english', etc.
        #when None, it implicitly means 'any', a.k.a. this column doesn't matter in QuerySet

        if event_purpose_name and language_name:

            self.form_event_purpose = EventPurposes.objects.get(event_purpose_name=event_purpose_name)
            self.form_language = Languages.objects.get(language_name=language_name)

        else:

            return False

        #self.form_event_tone is already None by default
        if event_tone_name:

            self.form_event_tone = EventTones.objects.get_or_create(event_tone_name=event_tone_name)[0]

        return True


    def create_event(
        self, form_when_trigger, form_event_name, form_event_message='',
        with_request=False, talker_user_id=None
    ):

        #when_trigger only accepts datetime object that is timezone-aware
        #event_name is required
        if\
            isinstance(form_when_trigger, datetime) is True and form_when_trigger.tzinfo == ZoneInfo('UTC')\
            and form_event_name\
            and (\
                (with_request is True and isinstance(talker_user_id, int)) or\
                (with_request is False and talker_user_id is None)\
            )\
        :

            pass

        else:

            raise ValueError('Arguments did not meet ListenerActions.create_event_with_request() requirements.')

        #we do not check for pending requests when creating new requests
        #if needed, in the future, we can do grouping on different users with identical event requests

        #handle event_status based on with_request
        event_status = None

        if with_request:

            event_status = EventStatuses.objects.get(event_status_name='request_pending')

        else:

            event_status = EventStatuses.objects.get(event_status_name='available')

        #create listener event
        self.listener_event = Events.objects.create(
            user_event_role = self.listener,
            event_purpose = self.form_event_purpose,
            language = self.form_language,
            event_tone = self.form_event_tone,
            event_status = event_status,
            event_name = form_event_name,
            event_message = form_event_message,
            when_trigger = form_when_trigger
        )

        #create event request
        if with_request:

            #find talker UserEventRole based on AuthUser.id given
            self.talker = UserEventRoles.objects.get(
                user__id = talker_user_id,
                event_role__event_role_name = 'talker'
            )

            #create
            self.event_request = EventRequests.objects.create(
                user_event_role = self.listener,
                requested_user_event_role = self.talker,
                event_request_status = EventRequestStatuses.objects.get(event_request_status_name='request_pending'),
                event = self.listener_event,
                payment_id = None,
            )

        return True


    #save listener ending_score and ending_message
    def save_listener_score_and_message(self, ending_score=None, ending_message=''):

        self.listener_event_room_match.ending_score = ending_score
        self.listener_event_room_match.ending_message = ending_message

        if ending_score is not None or ending_message is not None:

            self.listener_event_room_match.save()
        
        return True


    #contribute to talker's given_scores
    def apply_score_to_talker(self, ending_score=None):

        if ending_score is not None:

            self.talker.given_scores[ending_score] += 1
            self.talker.save()

        return True


    def release_payment_to_talker(self):

        #check if this is a paid request via listener_event on event_requests
        #set up EventRequestPayments and other necessary payment tables later
        try:

            self.event_request = EventRequests.objects.get(
                user_event_role=self.talker,
                event=self.talker_event,
                requested_user_event_role=self.listener,
                event_status=EventStatuses.objects.get(event_status_name='request_accepted'),
            )

            #release payments here

            self.event_request.payment_id = 'haha done'
            self.event_request.event_status = EventStatuses.objects.get(event_status_name='request_fulfilled')
            self.event_request.save()
        
        except EventRequests.DoesNotExist:
            
            #ok, this event is not a requested one
            pass

        except:

            #log here
            return False

        return True