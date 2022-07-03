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
from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework import routers

from voicewake import views

#register API URLs for auto-create
router = routers.SimpleRouter(trailing_slash=False)
router.register(r'api/user_verification_options', views.UserVerificationOptionsViewSet)

#original URL
urlpatterns = [
    path('admin', admin.site.urls),
    
    #APIs
    # path('user_verification_options/', views.user_verification_options_list),
    # path('user_verification_options/<int:id>/', views.user_verification_options_details),
    path('', include(router.urls)),
    
    #user management
    #refer to link below for all URLs/APIs already provided
    #https://github.com/django/django/blob/main/django/contrib/auth/urls.py
    path('', include('django.contrib.auth.urls')),

    # templates
    path('', views.home, name='home'),
    path('sign-up', views.sign_up, name='sign_up'),
    path('create-event', views.CreateEventView.as_view(), name='create_event'),
    path('set-timezone', views.set_timezone, name='set_timezone'),
    
]


#do this to enable specifying .json extension at URL
#currently off to try out routers
# urlpatterns = format_suffix_patterns(urlpatterns)