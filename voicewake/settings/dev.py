from .common import *


DEBUG = True


REQUEST_TIME_DELAY = 0  #seconds
SHOW_DJANGO_DEBUG_TOOLBAR = True


ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


#debug configs

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda r: SHOW_DJANGO_DEBUG_TOOLBAR,
}

#add these middleware to be earliest
MIDDLEWARE = [
    'voicewake.middleware.drf_api_delay_middleware.TimeDelayMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE

INSTALLED_APPS += [
    #debug
    'debug_toolbar'
]

#not needed, but required by django-debug-toolbar
if DEBUG is True:

    INTERNAL_IPS = [
        '127.0.0.1',
    ]


EVENT_INCOMPLETE_QUEUE_MAX_AGE_S = 99999999
