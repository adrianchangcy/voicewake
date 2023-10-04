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



def user_banned_events(request):

    if\
        request.user.is_authenticated is True and\
        request.user.banned_until is not None\
    :

        if request.user.banned_until > get_datetime_now():

            return render(
                request,
                template_name='voicewake/user_banned_events.html',
                context={
                    'banned_until': request.user.banned_until
                }
            )

        else:

            #unban
            request.user.banned_until = None
            request.user.save()

    return redirect(reverse('home'))



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
                reverse('user_profile', kwargs={'username': specific_user.username})
            )
        
        #check if blocked
        is_blocked = False

        if request.user.is_authenticated is True:

            is_blocked = UserBlocks.objects.filter(blocked_user=specific_user, user=request.user).exists()

        return render(
            request,
            template_name=self.template_name,
            context={
            'user_profile_username': specific_user.username,
            'is_own_profile': json.dumps(request.user.is_authenticated is True and request.user.id == specific_user.id),
            'is_blocked': json.dumps(is_blocked)
            }
        )



#create main events, but actual creation is via EventsAPI
#handles originator events
@method_decorator(
    [
        app_decorators.deny_if_not_logged_in("redirect"),
        app_decorators.deny_if_no_username("redirect"),
        app_decorators.deny_if_banned("redirect"),
    ],
    name='get'
)
class CreateEventRooms(TemplateView):

    template_name = 'voicewake/event_rooms/create_event_rooms.html'



#view specific event_room and its events
@method_decorator(
    [
        app_decorators.deny_if_no_username("redirect"),
        app_decorators.deny_if_banned("redirect"),
    ],
    name='get'
)
class GetEventRooms(TemplateView):

    template_name = 'voicewake/event_rooms/get_event_rooms.html'

    def get(self, request, *args, **kwargs):

        #get event_room
        try:

            event_room = EventRooms.objects.select_related('locked_for_user', 'generic_status').get(pk=kwargs['event_room_id'])

        except EventRooms.DoesNotExist:

            return JsonResponse(
                data={
                    'message':'Event room does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        #count how many events exist for frontend skeleton
        event_count = Events.objects.filter(
            event_room=event_room,
            generic_status__generic_status_name='ok'
        ).count()

        #check if this user is already supposed to reply
        is_this_user_replying = (
            self.request.user.is_authenticated and
            event_room.locked_for_user is not None and
            request.user.id == event_room.locked_for_user.id and
            event_room.is_replying is True
        )
        
        #is event_room deleted
        is_deleted = event_room.generic_status.generic_status_name == 'deleted'

        return render(
            request,
            template_name=self.template_name,
            context={
            'event_room_reply_choice_expiry_seconds': settings.EVENT_ROOM_REPLY_CHOICE_EXPIRY_SECONDS,
            'event_room_reply_expiry_seconds': settings.EVENT_ROOM_REPLY_EXPIRY_SECONDS,
            'event_room': event_room,
            'is_deleted': is_deleted,
            'is_deleted_json': json.dumps(is_deleted),
            'event_count': json.dumps(event_count),
            'is_this_user_replying': json.dumps(is_this_user_replying),
            }
        )



#for finding reply choices
@method_decorator(
    [
        app_decorators.deny_if_not_logged_in("redirect"),
        app_decorators.deny_if_no_username("redirect"),
        app_decorators.deny_if_banned("redirect"),
    ],
    name='get'
)
class ListEventRoomChoices(TemplateView):

    template_name = 'voicewake/event_rooms/list_event_room_choices.html'

    def get(self, request, *args, **kwargs):

        return render(
            request,
            template_name=self.template_name,
            context={
            'event_room_reply_choice_expiry_seconds': settings.EVENT_ROOM_REPLY_CHOICE_EXPIRY_SECONDS,
            'event_room_reply_expiry_seconds': settings.EVENT_ROOM_REPLY_EXPIRY_SECONDS,
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
                context={
                }
            )

        raise Http404()



