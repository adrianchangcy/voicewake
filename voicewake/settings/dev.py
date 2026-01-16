from .common import *
import sys


DEBUG = True
DEBUG_PROPAGATE_EXCEPTIONS = True   #shows detailed exceptions instead of simple 500


CORS_ALLOWED_ORIGINS += [
    f'https://{ os.environ['NGINX_DEV_MACHINE_STATIC_LAN_IP'] }',
]


CSRF_TRUSTED_ORIGINS += [
    #specify ":xxxx" to match whichever port NGINX is listening to
    #using HTTPS also prevents you from using HTTP, but it's worth it, because NGINX is now more integrated in dev workflow
    'https://127.0.0.1:8080',
    f'https://{ os.environ['NGINX_DEV_MACHINE_STATIC_LAN_IP'] }:8080',
]


#during tests, also use 'default' db
#by specifying ['TEST']['MIRROR'] to 'default', test queries to db will be redirected to real db
    #this also means that other types of test cases, like TransactionTestCase, that should roll back, will not roll back
#this overrides tests from creating their own db
DATABASES['default'].update({
    'TEST': {
        #'NAME' does not seem to matter but must be specified
        'NAME': 'test_' + DATABASES['default']['NAME'],
        #no 'MIRROR' key-value here, so we can use flag + custom runner and add 'MIRROR' whenever we want to use main db
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
    'voicewake.middleware.api_time_delay_middleware.APITimeDelayMiddleware',
] + MIDDLEWARE


#this is the starting portion of S3 path, since there's media/dev, media/stage, media/prod, etc.
#the API that determines paths of new files will use this
    #services.S3PostWrapper.generate_unprocessed_object_key
#for auto-generated rows, refer to one identical file from cloudfront, e.g. media/test/audio_ok_10s.webm
#serializer will serve absolute cloudfront paths to frontend, instead of redirecting at urls.py and eating server load
MEDIA_AWS_S3_START_PATH = 'media/dev'
MEDIA_TEST_AWS_S3_START_PATH = 'media/test'


#for MEDIA, always use S3
#fetch rows via serializer and have the serializer serve absolute paths using MEDIA_URL
    #serializers.AudioClipsSerializer.get_audio_file
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
MEDIA_ROOT = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
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



