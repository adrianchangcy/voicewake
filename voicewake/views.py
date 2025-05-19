from django.http import QueryDict
from django.db.models import Case, Value, When, Sum, Q, F, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.utils.cache import patch_cache_control
from django.db.models import Prefetch
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.http import Http404
from django.urls import reverse

#auth
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required

#DRF, class-based views
from rest_framework import status

#Django views
from django.views.generic.list import ListView
from django.views.generic import TemplateView

#mixins
from django.contrib.auth.mixins import PermissionRequiredMixin

#Python
# from datetime import datetime, timezone, timedelta
# from dateutil.relativedelta import relativedelta
import json

#app files
from voicewake.models import *
from voicewake.serializers import *
from voicewake.services import *
import voicewake.decorators as app_decorators
from django.conf import settings



#test only
#return callable
def test_page(template_name='test.html'):

    def render_callable(request, template_name=template_name):

        return render(request, template_name=template_name)

    return render_callable



@app_decorators.deny_if_banned("redirect")
@app_decorators.deny_if_no_username("redirect")
def home(request):

    return render(request, template_name='voicewake/home.html')



def about(request):

    return render(request, template_name='voicewake/about.html')



@app_decorators.deny_if_already_logged_in("redirect")
def log_in(request):

    return render(request, template_name='registration/log_in.html')



@app_decorators.deny_if_already_logged_in("redirect")
def sign_up(request):

    return render(request, template_name='registration/sign_up.html')



def user_banned_audio_clips(request):

    if\
        request.user.is_authenticated is True and\
        request.user.banned_until is not None\
    :

        if request.user.banned_until > get_datetime_now():

            return render(
                request,
                template_name='voicewake/user_banned_audio_clips.html',
                context={
                    'banned_until': request.user.banned_until
                }
            )

        else:

            #unban
            request.user.banned_until = None
            request.user.save()

    return redirect(reverse('home'), permanent=True)



@method_decorator(
    [
        app_decorators.deny_if_not_logged_in("redirect"),
        app_decorators.deny_if_no_username("redirect"),
    ],
    name='get'
)
class ListUserBlocks(TemplateView):

    template_name = 'voicewake/user_blocks.html'



@method_decorator(
    [
        app_decorators.deny_if_not_logged_in("redirect"),
        app_decorators.deny_if_no_username("redirect"),
    ],
    name='get'
)
class ListUserFollows(TemplateView):

    template_name = 'voicewake/user_follows.html'



@method_decorator(
    [
        app_decorators.deny_if_no_username("redirect"),
        app_decorators.deny_if_banned("redirect"),
        never_cache
    ],
    name='get'
)
class GetUserProfile(TemplateView):

    template_name = 'voicewake/user_profile.html'

    def get(self, request, *args, **kwargs):

        specific_user = get_object_or_404(get_user_model(), username_lowercase=kwargs['username'].lower())

        #redirect/change URL to respect username's case sensitivity
        if kwargs['username'] != specific_user.username:

            return redirect(
                reverse('user_profile', kwargs={'username': specific_user.username}),
                permanent=True
            )
        
        #check if blocked
        is_blocked = False
        is_following = False

        if request.user.is_authenticated is True:

            is_blocked = UserBlocks.objects.filter(blocked_user=specific_user, user=request.user).exists()
            is_following = UserFollows.objects.filter(followed_user=specific_user, user=request.user).exists()

        return render(
            request,
            template_name=self.template_name,
            context={
            'username': specific_user.username,
            'is_own_page': json.dumps(request.user.is_authenticated is True and request.user.id == specific_user.id),
            'is_blocked': json.dumps(is_blocked),
            'is_following': json.dumps(is_following),
            }
        )



@method_decorator(
    [
        app_decorators.deny_if_not_logged_in("redirect"),
        app_decorators.deny_if_no_username("redirect"),
        app_decorators.deny_if_banned("redirect"),
        never_cache
    ],
    name='get'
)
class ListUserLikesDislikes(TemplateView):

    template_name = 'voicewake/user_likes_dislikes.html'

    def get(self, request, *args, **kwargs):

        #users can only view their own likes/dislikes for now

        return render(
            request,
            template_name=self.template_name,
            context={
            'username': request.user.username,
            'is_own_page': json.dumps(True),
            }
        )



#create main audio_clips, but actual creation is via AudioClipsAPI
#handles originator audio_clips
@method_decorator(
    [
        app_decorators.deny_if_not_logged_in("redirect"),
        app_decorators.deny_if_no_username("redirect"),
        app_decorators.deny_if_banned("redirect"),
    ],
    name='get'
)
class CreateEvents(TemplateView):

    template_name = 'voicewake/events/create_events.html'



#view specific event and its audio_clips
@method_decorator(
    [
        app_decorators.deny_if_no_username("redirect"),
        app_decorators.deny_if_banned("redirect"),
    ],
    name='get'
)
class GetEvents(TemplateView):

    template_name = 'voicewake/events/get_events.html'

    def get(self, request, *args, **kwargs):

        #if user is reuploading, user shall be redirected with "?reupload=__", which is AudioClips.id
        #if user is truly replying, place "reupload_audio_clip_id"

        #get event
        try:

            event = Events.objects.select_related('generic_status').get(pk=kwargs['event_id'])

        except Events.DoesNotExist:

            return render(
                request,
                template_name='404.html',
                status=status.HTTP_404_NOT_FOUND
            )

        #check if event is deleted
        is_deleted = event.generic_status.generic_status_name == 'deleted'

        #prepare context early for consistency
        template_context = {
            'event_reply_choice_expiry_seconds': settings.EVENT_REPLY_CHOICE_MAX_DURATION_S,
            'event_reply_expiry_seconds': settings.EVENT_REPLY_MAX_DURATION_S,
            'audio_clip_unprocessed_expiry_seconds': settings.AUDIO_CLIP_UNPROCESSED_EXPIRY_S,
            'event': event,
            'is_deleted': is_deleted,
            'is_deleted_json': json.dumps(is_deleted),
        }

        if event.generic_status.generic_status_name not in ['processing', 'incomplete'] or is_deleted is True:

            return render(
                request,
                template_name=self.template_name,
                context=template_context
            )

        #has processing
        #check if user is here to reupload

        #get audio_clip_id if passed in GET params
        reupload_audio_clip_id = request.GET.get('reupload', None)

        if reupload_audio_clip_id is None:

            #not for reupload, show normal page
            return render(
                request,
                template_name=self.template_name,
                context=template_context
            )

        #validate
        serializer = GetEventsViewSerializer(data=request.GET)

        if serializer.is_valid() is False:

            return render(
                request,
                template_name=self.template_name,
                context=template_context
            )

        #user is here to reupload
        #prepare needed data at template for reupload

        reupload_audio_clip_id = serializer.validated_data['reupload']

        #also get AudioClipTones so we can refill form fields, aesthetic reasons only
        #you can just use Pinia and store + retrieve
        #but enabling cross-device feels important enough, e.g. user's device0 isn't good, so switch
        try:

            target_audio_clip = AudioClips.objects.select_related(
                'audio_clip_role',
                'audio_clip_tone',
            ).only(
                'audio_clip_role__audio_clip_role_name',
                'audio_clip_tone__id',
                'audio_clip_tone__audio_clip_tone_name',
                'audio_clip_tone__audio_clip_tone_slug',
                'audio_clip_tone__audio_clip_tone_symbol',
                'id',
            ).get(
                pk=reupload_audio_clip_id,
                user=request.user,
                generic_status__generic_status_name='processing',
            )

        except AudioClips.DoesNotExist:

            #user cannot reupload, just return normal page
            return render(
                request,
                template_name=self.template_name,
                context=template_context
            )

        #pass this back to template
        template_context.update({
            'is_reupload': True,
            'reupload_audio_clip_id_json': json.dumps(reupload_audio_clip_id),
            'reupload_audio_clip_role_name': target_audio_clip.audio_clip_role.audio_clip_role_name,
            'reupload_audio_clip_tone_id': target_audio_clip.audio_clip_tone.id,
            'reupload_audio_clip_tone_name': target_audio_clip.audio_clip_tone.audio_clip_tone_name,
            'reupload_audio_clip_tone_slug': target_audio_clip.audio_clip_tone.audio_clip_tone_slug,
            'reupload_audio_clip_tone_symbol': target_audio_clip.audio_clip_tone.audio_clip_tone_symbol,
        })

        return render(
            request,
            template_name=self.template_name,
            context=template_context
        )

        # patch_cache_control(
        #     response,
        #     no_cache=True, no_store=True, must_revalidate=True, max_age=0
        # )



#for finding reply choices
@method_decorator(
    [
        app_decorators.deny_if_not_logged_in("redirect"),
        app_decorators.deny_if_no_username("redirect"),
        app_decorators.deny_if_banned("redirect"),
    ],
    name='get'
)
class EventReplyChoices(TemplateView):

    template_name = 'voicewake/events/list_event_reply_choices.html'

    def get(self, request, *args, **kwargs):

        return render(
            request,
            template_name=self.template_name,
            context={
            'event_reply_choice_expiry_seconds': settings.EVENT_REPLY_CHOICE_MAX_DURATION_S,
            'event_reply_expiry_seconds': settings.EVENT_REPLY_MAX_DURATION_S,
            'audio_clip_unprocessed_expiry_seconds': settings.AUDIO_CLIP_UNPROCESSED_EXPIRY_S,
            }
        )



#for new username
#once set, any GET attempt will return 404
@method_decorator(never_cache, name='get')
class SetUsername(TemplateView):

    template_name = 'registration/set_username.html'
    
    def get(self, request, *args, **kwargs):

        #can continue
        if(
            request.user.is_authenticated is True and
            request.user.banned_until is None and
            request.user.username_lowercase is None
        ):

            return render(
                request,
                template_name=self.template_name,
                context={},
            )

        raise Http404()



class UnderMaintenance(TemplateView):

    template_name = '503.html'

    def get(self, request, *args, **kwargs):

        if settings.MAINTENANCE_MODE is True:

            return render(
                request,
                template_name=self.template_name,
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return redirect(reverse('home'))





