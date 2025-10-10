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
        user_is_banned = False
        user_banned_until = None
        user_ban_count = 0
        user_is_active = True

    email = factory.LazyAttributeSequence(
        lambda o, n : 'user'+str(n)+'@gmail.com' if o.user_email == '' else o.user_email
    )
    username = factory.LazyAttributeSequence(
        lambda o, n : 'useR'+str(n) if o.user_username == '' else o.user_username
    )
    is_banned = factory.LazyAttribute(
        lambda o : o.user_is_banned
    )
    banned_until = factory.LazyAttribute(
        lambda o : (
            get_datetime_now() + timedelta(days=o.user_ban_count)
            if o.user_is_banned is True
            else None
        )
    )
    ban_count = factory.LazyAttribute(lambda o : o.user_ban_count)
    is_active = factory.LazyAttribute(lambda o : o.user_is_active)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):

        manager = cls._get_manager(model_class)

        new_user = manager.create_user(
            email=kwargs['email'],
            username=kwargs['username'],
            is_active=kwargs['is_active'],
        )

        #oddly, must explicitly define all fields here, else they will be missing in instance returned from save()
        new_user.is_banned = kwargs['is_banned']
        new_user.banned_until = kwargs['banned_until']
        new_user.ban_count = kwargs['ban_count']
        new_user.save()

        return new_user



class EventsFactory(DjangoModelFactory):

    class Meta:
        model = Events

    class Params:
        event_event_name = ''
        event_created_by = None
        event_generic_status_generic_status_name = ''

    created_by = factory.LazyAttribute(
        lambda o : (
            UsersFactory()
            if o.event_created_by is None
            else o.event_created_by
        )
    )
    event_name = factory.LazyAttribute(
        lambda o : (
            'test event' if o.event_event_name == '' else o.event_event_name
        )
    )
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
        audio_clip_generic_status_generic_status_name = 'ok'
        audio_clip_is_banned = False
        audio_clip_audio_file = 'test/audio_ok_10s.webm'    #S3
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
            if o.audio_clip_generic_status_generic_status_name in ['processing_pending', 'processing', 'processing_failed']
            else o.audio_clip_audio_volume_peaks
        )
    )
    audio_duration_s = factory.LazyAttribute(
        lambda o : (
            0
            if o.audio_clip_generic_status_generic_status_name in ['processing_pending', 'processing', 'processing_failed']
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
                    generic_status_name=('deleted' if o.is_banned is True else 'ok')
                )
            )
        )
    )



class AudioClipMetricsFactory(DjangoModelFactory):

    class Meta:
        model = AudioClipMetrics

    class Params:
        audio_clip_metric_audio_clip = None
        audio_clip_metric_like_count = 0
        audio_clip_metric_dislike_count = 0
        audio_clip_metric_like_ratio = 0

    audio_clip = factory.LazyAttribute(
        lambda o : o.audio_clip_metric_audio_clip
    )
    like_count = factory.LazyAttribute(
        lambda o : o.audio_clip_metric_like_count
    )
    dislike_count = factory.LazyAttribute(
        lambda o : o.audio_clip_metric_dislike_count
    )
    like_ratio = factory.LazyAttribute(
        lambda o : o.audio_clip_metric_like_ratio
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





