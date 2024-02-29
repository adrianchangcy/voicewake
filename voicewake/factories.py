from factory.django import DjangoModelFactory
import factory

from django.contrib.auth import get_user_model

from voicewake.models import *
from voicewake.services import *



#usage guide
#incomplete events
    #just use AudioClipsFactory(), and everything else will also be auto-created
    #optional, can specify user



class UsersFactory(DjangoModelFactory):

    class Meta:
        model = get_user_model()
        django_get_or_create = ('username_lowercase',)

    class Params:
        user_email = ''
        user_username = ''

    email = factory.LazyAttributeSequence(
        lambda o, n : 'user'+str(n)+'@gmail.com' if o.user_email == '' else o.user_email
    )
    username = factory.LazyAttributeSequence(
        lambda o, n : 'useR'+str(n) if o.user_username == '' else o.user_username
    )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):

        manager = cls._get_manager(model_class)

        is_user_created = get_user_model().objects.filter(
            email_lowercase=kwargs['email'].lower(),
            username_lowercase=kwargs['username'].lower(),
        )

        if is_user_created is False:

            return manager.create_user(
                kwargs['email'],
                kwargs['username'],
                True
            )



class EventsFactory(DjangoModelFactory):

    class Meta:
        model = Events

    class Params:
        event_created_by = None
        event_generic_status_generic_status_name = ''

    created_by = factory.LazyAttribute(
        lambda o : (
            UsersFactory()
            if o.event_created_by is None
            else o.event_created_by
        )
    )
    event_name = 'test event'
    generic_status = factory.LazyAttribute(
        lambda o : (
            GenericStatuses.objects.get(
                generic_status_name=o.event_generic_status_generic_status_name
            )
        )
    )



class AudioClipsFactory(DjangoModelFactory):

    class Meta:
        model = AudioClips

    class Params:
        audio_clip_user = None
        audio_clip_audio_clip_role_audio_clip_role_name = 'originator'
        audio_clip_event = None
        audio_file_object_key = ''
        audio_clip_generic_status_generic_status_name = 'ok'
        audio_clip_is_banned = False
        audio_clip_audio_file = 'audio_test.mp3'
        audio_clip_audio_volume_peaks = [
            0.32, 0.47, 0.76, 0.75, 0.79, 0.59, 0.78, 0.83, 0.85, 0.77,
            0.62, 0.69, 0.97, 0.96, 0.97, 0.96, 0.96, 0.63, 0.47, 0.0
        ]
        audio_clip_audio_duration_s = 26

    user = factory.LazyAttribute(
        lambda o : (
            UsersFactory()
            if o.audio_clip_user == None
            else o.audio_clip_user
        )
    )
    audio_clip_role = factory.LazyAttribute(
        lambda o : AudioClipRoles.objects.get(audio_clip_role_name=o.audio_clip_audio_clip_role_audio_clip_role_name)
    )
    audio_clip_tone = AudioClipTones.objects.all().first()
    audio_file = factory.LazyAttribute(lambda o : o.audio_clip_audio_file)
    audio_volume_peaks = factory.LazyAttribute(
        lambda o : (
            []
            if o.audio_clip_generic_status_generic_status_name == 'processing'
            else o.audio_clip_audio_volume_peaks
        )
    )
    audio_duration_s = factory.LazyAttribute(
        lambda o : (
            0
            if o.audio_clip_generic_status_generic_status_name == 'processing'
            else o.audio_clip_audio_duration_s
        )
    )
    is_banned = factory.LazyAttribute(lambda o : o.audio_clip_is_banned)
    generic_status = factory.LazyAttribute(
        lambda o : GenericStatuses.objects.get(
            generic_status_name=o.audio_clip_generic_status_generic_status_name
        )
    )
    event = factory.LazyAttribute(
        lambda o : (
            o.audio_clip_event
            if o.audio_clip_event != None
            else (
                EventsFactory(
                    created_by=(o.audio_clip_user if o.audio_clip_user is not None else UsersFactory()),
                    event_generic_status_generic_status_name=('deleted' if o.audio_clip_is_banned is True else 'ok')
                )
            )
        )
    )



class AudioClipReportsFactory(DjangoModelFactory):

    class Meta:
        model = AudioClipReports

    class Params:
        audio_clip_report_audio_clip = None
        is_already_banned = False

    audio_clip = factory.LazyAttribute(
        lambda o : o.audio_clip_report_audio_clip
    )
    last_evaluated = factory.LazyAttribute(
        lambda o : get_datetime_now() if o.is_already_banned is True else (get_datetime_now() - timedelta(seconds=10))
    )
    last_reported = factory.LazyAttribute(
        lambda o : (get_datetime_now() - timedelta(seconds=10)) if o.is_already_banned is True else get_datetime_now()
    )





