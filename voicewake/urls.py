"""voicewake URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import routers
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from voicewake import views
from voicewake import apis

#register API URLs for auto-create
router = routers.SimpleRouter(trailing_slash=False)
# router.register(r'api/event-tones', views.EventTonesAPI)

#original URL
urlpatterns = [
    path('admin', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),

    
    #APIs

    #we don't need default urls
    # path('', include(router.urls)),

    path('api/test', apis.TestAPI.as_view(), name='test'),

    path('api/event-rooms/get/<int:event_room_id>', apis.EventRoomsAPI.as_view(), name='get_event_rooms_by_event_room_id'),

    path('api/event-rooms/list/completed/<str:latest_or_best>/<str:timeframe>/<int:page>', apis.EventRoomsAPI.as_view(), name='get_event_rooms_by_best_or_new_paged'),
    path('api/event-rooms/list/completed/<str:latest_or_best>/<str:timeframe>/<str:event_tone_slug>/<int:page>', apis.EventRoomsAPI.as_view(), name='get_event_rooms'),
    path('api/event-rooms/list/user/<str:username>/<str:latest_or_best>/<str:timeframe>/<str:event_role_name>/<int:page>', apis.EventRoomsAPI.as_view(), name='get_event_rooms'),
    path('api/event-rooms/list/user/<str:username>/<str:latest_or_best>/<str:timeframe>/<str:event_role_name>/<str:event_tone_slug>/<int:page>', apis.EventRoomsAPI.as_view(), name='get_event_rooms'),

    path('api/event-rooms/reply-choices/list', apis.HandleEventRoomReplyChoicesAPI.as_view(current_context="list"), name="list_event_room_choices"),
    path('api/event-rooms/reply-choices/expire', apis.HandleEventRoomReplyChoicesAPI.as_view(current_context="expire"), name="expire_event_room_choices"),

    path('api/event-rooms/create-new', apis.EventsAPI.as_view(current_context="create_new"), name='create_new_event_rooms'),
    path('api/event-rooms/reply/start', apis.HandleReplyingEventRoomsAPI.as_view(current_context="start"), name="start_reply_event_rooms"),
    path('api/event-rooms/reply', apis.EventsAPI.as_view(current_context="reply"), name="reply_event_rooms"),
    path('api/event-rooms/reply/cancel', apis.HandleReplyingEventRoomsAPI.as_view(current_context="cancel"), name="cancel_reply_event_rooms"),

    path('api/event-reports/create', apis.EventReportsAPI.as_view(), name="create_event_reports"),
    path('api/event-report-bans/get', apis.EventReportBansAPI.as_view(), name="get_event_report_bans"),

    path('api/event-tones/list', apis.EventTonesAPI.as_view(), name='event_tones'),
    path('api/event-likes-dislikes', apis.EventLikesDislikesAPI.as_view(), name='event_likes_dislikes'),
    path('api/users/blocks', apis.UserBlocksAPI.as_view(), name='users_block_users'),
    path('api/users/username/get/<str:username>', apis.UsersUsernameAPI.as_view(), name='users_get_username'),
    path('api/users/username/set', apis.UsersUsernameAPI.as_view(), name='users_set_username'),
    path('api/users/sign-up', apis.UsersLogInSignUpAPI.as_view(current_context='sign_up'), name='users_sign_up'),
    path('api/users/log-in', apis.UsersLogInSignUpAPI.as_view(current_context='log_in'), name='users_log_in'),
    path('api/users/log-out', apis.UsersLogOutAPI.as_view(), name='users_log_out'),
    
    #user management
    #refer to link below for all URLs/APIs already provided
    #https://github.com/django/django/blob/main/django/contrib/auth/urls.py
    # path('', include('django.contrib.auth.urls')),

    #allauth for Google, etc.
    # path('accounts/', include('allauth.urls')),

    # templates
    #still need to make these pretty, but leave it for last
    #we specify 'name' arg for auto-construction of full URL via reverse()
    path('', views.home, name='home'),
    path('login', views.log_in, name='log_in'),
    path('signup', views.sign_up, name='sign_up'),
    path('banned', views.user_banned, name='user_banned'),

    path('user/<str:username>', views.GetUserProfile.as_view(), name='user_profile'),
    path('username/new', views.SetUsername.as_view(), name='set_username'),
    path('start', views.CreateEventRooms.as_view(), name='create_event_rooms'),
    path('reply', views.ListEventRoomChoices.as_view(), name='list_event_room_choices'),
    path('hear/<int:event_room_id>', views.GetEventRooms.as_view(), name='get_event_rooms'),

    #favicon
    #only for tab icon, not to be used as actual svg
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('tab-icon.svg'))),
]

#for media files
if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


#do this to enable specifying .json extension at URL
#currently off to try out routers
# urlpatterns = format_suffix_patterns(urlpatterns)