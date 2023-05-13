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

#register API URLs for auto-create
router = routers.SimpleRouter(trailing_slash=False)
router.register(r'api/event-tones', views.EventTonesAPI)

#original URL
urlpatterns = [
    path('admin', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),

    
    #APIs
    # path('user_verification_options/', views.user_verification_options_list),
    # path('user_verification_options/<int:id>/', views.user_verification_options_details),
    path('', include(router.urls)),
    path('api/events/get/event-room/<int:event_room_id>', views.EventsAPI.as_view(), name='get_events_by_event_room_id'),
    path('api/events/get/event-room/status/<str:generic_status_name>', views.EventsAPI.as_view(), name='get_events_by_generic_status_name'),
    path('api/events/create', views.EventsAPI.as_view(), name='create_events'),
    path('api/event-likes-dislikes', views.EventLikesDislikesAPI.as_view(), name='event_likes_dislikes'),
    path('api/user-actions', views.UserActionsAPI.as_view(), name='user_actions'),
    
    #user management
    #refer to link below for all URLs/APIs already provided
    #https://github.com/django/django/blob/main/django/contrib/auth/urls.py
    path('', include('django.contrib.auth.urls')),

    # templates
    #still need to make these pretty, but leave it for last
    #we specify 'name' arg for auto-construction of full URL via reverse()
    path('', views.home, name='home'),
    path('sign-up', views.sign_up, name='sign_up'),
    path('say', views.CreateEventRooms.as_view(), name='create_event_room'),
    path('hear', views.ListEventRooms.as_view(), name='list_event_rooms'),
    path('hear/<int:event_room_id>', views.GetEventRooms.as_view(), name='get_event_room'),
    # path('reply', views.ReplyMainEventsFormView.as_view(), name='reply_new_events'),
    # path('seek-event', views.SeekEventsFormView.as_view(), name='seek_events'),

    #favicon
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('website-logo.svg'))),
]

#for media files
if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


#do this to enable specifying .json extension at URL
#currently off to try out routers
# urlpatterns = format_suffix_patterns(urlpatterns)