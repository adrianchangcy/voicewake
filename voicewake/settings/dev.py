from .common import *
import sys


DEBUG = True
DEBUG_PROPAGATE_EXCEPTIONS = True   #shows detailed exceptions instead of simple 500


#during tests, also use 'default' db
#by specifying ['TEST']['MIRROR'] to 'default', test queries to db will be redirected to real db
    #this also means that other types of test cases, like TransactionTestCase, that should roll back, will not roll back
#this overrides tests from creating their own db
DATABASES['default'].update({
    'TEST': {
        #'NAME' does not seem to matter but must be specified
        'NAME': 'test_' + DATABASES['default']['NAME'],
    },
})


REQUEST_TIME_DELAY = 0  #seconds


#fix for tests being unable to run due to debug toolbar
#DEBUG=False does not guarantee toolbar won't initialise, so only way is to prevent adding it to INSTALLED_APPS
#old solution was to set DEBUG_TOOLBAR_CONFIG['SHOW_TOOLBAR_CALLBACK'] to False
#https://github.com/django-commons/django-debug-toolbar/issues/1920
ENABLE_DEBUG_TOOLBAR = DEBUG is True and "test" not in sys.argv

if ENABLE_DEBUG_TOOLBAR is True:

    #add as earliest
    INSTALLED_APPS = [
        "debug_toolbar",
    ] + INSTALLED_APPS

    #add as earliest
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    ] + MIDDLEWARE


TEMPLATES[0]['OPTIONS']['context_processors'].extend([
    'django.template.context_processors.debug',
])


#add these middleware to be earliest
MIDDLEWARE = [
    'voicewake.middleware.drf_api_delay_middleware.TimeDelayMiddleware',
] + MIDDLEWARE


MEDIAFILES_LOCATION = 'media/dev'
AWS_S3_CUSTOM_DOMAIN = os.environ['AWS_S3_CUSTOM_DOMAIN']


#for MEDIA, always use S3
#low cost even for testing, and also due to how integrated the S3 processes are to our code base
#implementing local file upload procedures would be redundant
BASE_S3_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

#from S3
# MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/'
# MEDIA_ROOT = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/'

#from local files
MEDIA_URL = 'media/'
MEDIA_ROOT = 'voicewake/tests/file_samples'

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'deploy/static')


#not needed, but required by django-debug-toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]


#FOR EASIER TESTS
EVENT_CREATE_DAILY_LIMIT = 99999      #compares from 00:00:00 UTC
EVENT_REPLY_DAILY_LIMIT = 99999       #compares from 00:00:00 UTC
EVENT_INCOMPLETE_QUEUE_MAX_AGE_S = 99999999
AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS = 3


#HTTPS
#might not be needed when we have nginx
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True



