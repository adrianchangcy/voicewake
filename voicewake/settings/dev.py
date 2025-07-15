from .common import *


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
SHOW_DJANGO_DEBUG_TOOLBAR = False


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


#add these middleware to be latest
MIDDLEWARE = MIDDLEWARE + [
]


INSTALLED_APPS = [
    'debug_toolbar',
] + INSTALLED_APPS


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



