from django.http import JsonResponse, QueryDict
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



def test_page(request):

    return render(request, template_name='test.html')



# @login_required(login_url='/login')
@app_decorators.deny_if_banned("redirect")
@app_decorators.deny_if_no_username("redirect")
def home(request):

    return render(request, template_name='voicewake/home.html')



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

        if request.user.is_authenticated is True:

            is_blocked = UserBlocks.objects.filter(blocked_user=specific_user, user=request.user).exists()

        return render(
            request,
            template_name=self.template_name,
            context={
            'username': specific_user.username,
            'is_own_page': json.dumps(request.user.is_authenticated is True and request.user.id == specific_user.id),
            'is_blocked': json.dumps(is_blocked)
            }
        )



@method_decorator(
    [
        app_decorators.deny_if_no_username("redirect"),
        app_decorators.deny_if_banned("redirect"),
        app_decorators.deny_if_not_logged_in("redirect"),
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

        #get event
        try:

            event = Events.objects.select_related('generic_status').get(pk=kwargs['event_id'])

        except Events.DoesNotExist:

            return JsonResponse(
                data={
                    'message':'Event does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        #count how many audio_clips exist for frontend skeleton
        audio_clip_count = AudioClips.objects.filter(
            event=event,
            generic_status__generic_status_name='ok'
        ).count()

        #prepare info
        is_deleted = event.generic_status.generic_status_name == 'deleted'

        #is event deleted

        response = render(
            request,
            template_name=self.template_name,
            context={
            'event_reply_choice_expiry_seconds': settings.EVENT_REPLY_CHOICE_MAX_DURATION_S,
            'event_reply_expiry_seconds': settings.EVENT_REPLY_MAX_DURATION_S,
            'event': event,
            'is_deleted': is_deleted,
            'is_deleted_json': json.dumps(is_deleted),
            'audio_clip_count': json.dumps(audio_clip_count),
            }
        )

        # patch_cache_control(
        #     response,
        #     no_cache=True, no_store=True, must_revalidate=True, max_age=0
        # )

        return response



#for finding reply choices
@method_decorator(
    [
        app_decorators.deny_if_not_logged_in("redirect"),
        app_decorators.deny_if_no_username("redirect"),
        app_decorators.deny_if_banned("redirect"),
    ],
    name='get'
)
class ListEventReplyChoices(TemplateView):

    template_name = 'voicewake/events/list_event_reply_choices.html'

    def get(self, request, *args, **kwargs):

        return render(
            request,
            template_name=self.template_name,
            context={
            'event_reply_choice_expiry_seconds': settings.EVENT_REPLY_CHOICE_MAX_DURATION_S,
            'event_reply_expiry_seconds': settings.EVENT_REPLY_MAX_DURATION_S,
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





