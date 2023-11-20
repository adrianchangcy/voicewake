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
# router.register(r'api/audio-clip-tones', views.AudioClipTonesAPI)

#URLs
urlpatterns = []

if settings.DEBUG is True:

    urlpatterns += [
        path('admin', admin.site.urls),
        path('__debug__/', include('debug_toolbar.urls')),
        path('api/test', apis.TestAPI.as_view(), name='test_api'),
        path('test', views.test_page, name='test_page'),
    ]

urlpatterns += [

    #we don't need default URLs
    # path('', include(router.urls)),

    path('api/events/list/completed/user/<str:username>/<str:latest_or_best>/<str:timeframe>/<str:audio_clip_role_name>/<int:audio_clip_tone_id>/<str:next_or_back>/<str:cursor_token>', apis.BrowseEventsAPI.as_view(), name='browse_events_api'),
    path('api/events/list/completed/user/<str:username>/<str:latest_or_best>/<str:timeframe>/<str:audio_clip_role_name>/<int:audio_clip_tone_id>/<str:next_or_back>', apis.BrowseEventsAPI.as_view(), name='browse_events_api'),
    path('api/events/list/completed/user/<str:username>/<str:latest_or_best>/<str:timeframe>/<str:audio_clip_role_name>/<str:next_or_back>/<str:cursor_token>', apis.BrowseEventsAPI.as_view(), name='browse_events_api'),
    path('api/events/list/completed/user/<str:username>/<str:latest_or_best>/<str:timeframe>/<str:audio_clip_role_name>/<str:next_or_back>', apis.BrowseEventsAPI.as_view(), name='browse_events_api'),

    path('api/events/list/completed/<str:latest_or_best>/<str:timeframe>/<str:audio_clip_role_name>/<int:audio_clip_tone_id>/<str:next_or_back>/<str:cursor_token>', apis.BrowseEventsAPI.as_view(), name='browse_events_api'),
    path('api/events/list/completed/<str:latest_or_best>/<str:timeframe>/<str:audio_clip_role_name>/<int:audio_clip_tone_id>/<str:next_or_back>', apis.BrowseEventsAPI.as_view(), name='browse_events_api'),
    path('api/events/list/completed/<str:latest_or_best>/<str:timeframe>/<str:audio_clip_role_name>/<str:next_or_back>/<str:cursor_token>', apis.BrowseEventsAPI.as_view(), name='browse_events_api'),
    path('api/events/list/completed/<str:latest_or_best>/<str:timeframe>/<str:audio_clip_role_name>/<str:next_or_back>', apis.BrowseEventsAPI.as_view(), name='browse_events_api'),

    path('api/events/create', apis.CreateEventsAPI.as_view(), name='create_events_api'),
    path('api/events/replies/choices/list', apis.ListEventReplyChoicesAPI.as_view(), name="list_event_reply_choices_api"),
    path('api/events/replies/start', apis.HandleReplyingEventsAPI.as_view(current_context="start"), name="start_replies_api"),
    path('api/events/replies/create', apis.HandleReplyingEventsAPI.as_view(current_context="reply"), name="create_replies_api"),
    path('api/events/replies/cancel', apis.HandleReplyingEventsAPI.as_view(current_context="cancel"), name="cancel_replies_api"),
    path('api/events/get/<int:event_id>', apis.GetEventsAPI.as_view(), name='get_events_api'),

    path('api/audio-clips/reports', apis.AudioClipReportsAPI.as_view(), name="create_audio_clip_reports_api"),
    path('api/audio-clips/tones', apis.AudioClipTonesAPI.as_view(), name='audio_clip_tones_api'),
    path('api/audio-clips/likes-dislikes', apis.AudioClipLikesDislikesAPI.as_view(), name='audio_clip_likes_dislikes_api'),
    path('api/audio-clips/bans/<str:username>/list/<str:next_or_back>/<str:cursor_token>', apis.UserBannedAudioClipsAPI.as_view(), name="user_banned_audio_clips_api"),
    path('api/audio-clips/bans/<str:username>/list/<str:next_or_back>', apis.UserBannedAudioClipsAPI.as_view(), name="user_banned_audio_clips_api"),

    path('api/users/blocks/<str:username>/list', apis.UserBlocksAPI.as_view(), name='list_user_blocks_api'),
    path('api/users/blocks', apis.UserBlocksAPI.as_view(), name='user_blocks_api'),
    path('api/users/username/get/<str:username>', apis.UsersUsernameAPI.as_view(), name='users_get_username_api'),
    path('api/users/username/set', apis.UsersUsernameAPI.as_view(), name='users_set_username_api'),
    path('api/users/sign-up', apis.UsersLogInSignUpAPI.as_view(current_context='sign_up'), name='users_sign_up_api'),
    path('api/users/log-in', apis.UsersLogInSignUpAPI.as_view(current_context='log_in'), name='users_log_in_api'),
    path('api/users/log-out', apis.UsersLogOutAPI.as_view(), name='users_log_out_api'),
    
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
    path('banned', views.user_banned_audio_clips, name='user_banned'),

    path('block', views.ListUserBlocks.as_view(), name='user_blocks'),
    path('user/<str:username>', views.GetUserProfile.as_view(), name='user_profile'),
    path('username/new', views.SetUsername.as_view(), name='set_username'),
    path('start', views.CreateEvents.as_view(), name='create_events'),
    path('reply', views.ListEventReplyChoices.as_view(), name='list_event_reply_choices'),
    path('event/<int:event_id>', views.GetEvents.as_view(), name='get_events'),
    path('maintenance', views.UnderMaintenance.as_view(), name='under_maintenance'),

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