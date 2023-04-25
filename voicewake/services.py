#here, we define business logic

#Django libraries
from django.db.models import Q, Case, When, Value
from django.db import connection
from django.core.files import File

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
from .static.values.values import *



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
                # event.event_status = EventStatuses.objects.get(event_status_name='file_ready')

                f.close()

        except:

            #handle faulty file
            event.audio_file = None
            # event.event_status = EventStatuses.objects.get(event_status_name='file_error')

            continue

    Events.objects.bulk_update(events, ['event_status', 'audio_file'])

    for old_file in old_files_to_delete:

        if os.path.isfile(old_file):

            os.remove(old_file)

    return True


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


#unlock events that have been locked for a user
def unlock_event_rooms_by_user(user_id):

    datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))

    return EventRooms.objects.filter(
        locked_for_user=AuthUser(pk=user_id)
    ).update(
        when_locked=None,
        locked_for_user=None,
        last_modified=datetime_now
    )


#unlock EventRooms that users have locked and abandoned
#if user has not abandoned, JS will ping to update EventRooms.when_locked, i.e. relock
def unlock_event_rooms_by_time():

    datetime_now = datetime.now().astimezone(tz=ZoneInfo('UTC'))
    checkpoint_datetime = datetime_now - timedelta(minutes=MINUTES_TO_UNLOCK_EVENT_ROOM)

    return EventRooms.objects.filter(
        when_locked__lte=checkpoint_datetime
    ).update(
        when_locked=None,
        locked_for_user=None,
        last_modified=datetime_now
    )

