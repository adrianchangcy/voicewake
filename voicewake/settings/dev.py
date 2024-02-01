from .common import *


DEBUG = True


REQUEST_TIME_DELAY = 0  #seconds
SHOW_DJANGO_DEBUG_TOOLBAR = True


ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


#hide/show debug toolbar, may cause issues when shown during tests
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda r: SHOW_DJANGO_DEBUG_TOOLBAR,
}


TEMPLATES[0]['OPTIONS']['context_processors'].extend([
    'django.template.context_processors.debug',
])


#add these middleware to be earliest
MIDDLEWARE = [
    'voicewake.middleware.drf_api_delay_middleware.TimeDelayMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE


INSTALLED_APPS = [
    'debug_toolbar'
] + INSTALLED_APPS


USE_S3 = False
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, MEDIA_URL)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'deploy/static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


#not needed, but required by django-debug-toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]


EVENT_INCOMPLETE_QUEUE_MAX_AGE_S = 99999999
