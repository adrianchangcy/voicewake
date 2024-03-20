from .common import *


DEBUG = True
DEBUG_PROPAGATE_EXCEPTIONS = True   #shows detailed exceptions instead of simple 500


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
    'debug_toolbar',
] + INSTALLED_APPS


MEDIAFILES_LOCATION = 'media/test'
AWS_S3_CUSTOM_DOMAIN = os.environ['AWS_S3_CUSTOM_DOMAIN']


#for MEDIA, always use S3
#low cost even for testing, and also due to how integrated the S3 processes are to our code base
#implementing local file upload procedures would be redundant
BASE_S3_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/'
MEDIA_ROOT = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/'
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'deploy/static')


#not needed, but required by django-debug-toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]


EVENT_INCOMPLETE_QUEUE_MAX_AGE_S = 99999999
