from pathlib import Path
import dotenv
import os
from socket import gethostname, gethostbyname
import boto3



#DJANGO_SETTINGS_MODULE
#Django will auto-find this in env vars to decide which to use, i.e. dev/stage/prod.py at settings



#find and load .env file
#for local, we load .env file manually
#for AWS, we specify stage.env or prod.env from S3, and the variables will be populated in
#if must use .env file in stage/prod, rename the file to .env to copy to destination, and ensure only 1 exists
env_path = dotenv.find_dotenv(filename='env/.env')

if len(env_path) != 0:

    dotenv.load_dotenv(env_path)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


#lazy but simple and effective solution, passed via context_processors.py
#look into ManifestStaticFileStorage to automate this by adding hash to file names
STATIC_CACHE_BUST_PREFIX = '?version='
STATIC_CACHE_BUST_VERSION = STATIC_CACHE_BUST_PREFIX + '1.0.0'


MAINTENANCE_MODE = int(os.environ.get('MAINTENANCE_MODE', 0)) == 1


#this dictates if secrets should be explicit at boto3 args, since AWS services will autofill when omitted
IS_EC2 = int(os.environ.get('IS_EC2', 0)) == 1


#SECURITY WARNING: keep the secret key used in production secret
#must use fixed SECRET_KEY for Django to sign session cookies
#else if always using new SECRET_KEY, it would kill all existing sessions
SECRET_KEY = os.environ['SECRET_KEY']


#assuming your env var is as so: ALLOWED_HOSTS=domain.com,anotherdomain.com
#dev is "*", but don't use as default, in case lacking .env in prod makes this disastrous
ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(",")


#AWS load balancer healthcheck will ping by using its own IP address in Host header
#if not included in ALLOWED_HOSTS, will throw 400 in healthcheck and entire ECS will fail soon enough via circuit breaker
#not sure if there is a race condition, but so far so good
ALLOWED_HOSTS.append(gethostbyname(gethostname()))


#middleware
MIDDLEWARE = []


if MAINTENANCE_MODE is True:

    MIDDLEWARE += [
        'voicewake.middleware.under_maintenance_middleware.UnderMaintenanceMiddleware',
    ]


#standard middlewares
MIDDLEWARE += [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'lockdown.middleware.LockdownMiddleware',
]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',     #if 1 db and multiple sites, use this and SITE_ID

    #lockdown to make site private
    'lockdown',

    #Celery
    "django_celery_beat",
    "django_celery_results",

    'rest_framework',
    #optional, provides template when returning Response() and not JsonResponse()
    #Django expects this when returning Response(), else error TemplateDoesNotExist ... rest_framework/api.html

    #app from apps.py
    'voicewake.apps.VoicewakeConfig',

    #token for DRF
    'rest_framework.authtoken',

    #channels for websocket
    # 'channels',

    #CORS, allows code in current domain to dynamically make requests to other domains, e.g. CloudFront
    #<link> does not count
    # 'corsheaders',

    #OTP
    'django_otp',
    # 'django_otp.plugins.otp_totp',
    # 'django_otp.plugins.otp_hotp',
    # 'django_otp.plugins.otp_static',

    #allauth
    # 'allauth',
    # 'allauth.account',
    # 'allauth.socialaccount',

    #social providers
    # 'allauth.socialaccount.providers.google',
]


CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://127.0.0.1:8080',
    'http://192.168.1.200:8080',
    'https://voicewake.com',
    'https://stage.voicewake.com',
    'https://' + os.environ['AWS_S3_CUSTOM_DOMAIN'],
]


CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://127.0.0.1:8080',
    'http://192.168.1.200:8080',
    'https://voicewake.com',
    'https://stage.voicewake.com',
]


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    #create available formatters
    'formatters': {
        'verbose': {
            'format': '%(asctime)s - %(levelname)s - %(message)s',
        },
        'simple': {
            'format' : '%(message)s',
        },
    },
    'handlers': {
    },
    'loggers': {
        #use logger=logging.getLogger('key_name') to specify from one of these loggers
        #levels consist of: DEBUG < INFO < WARNING < ERROR/EXCEPTION < CRITICAL
        #ensure that when you log, e.g. logger.info(), that it has equal or higher severity level
        #else it is not logged
    },
}


#logging specification
#note that logging to CloudWatch is not immediate, since there seems to be around a minute of delay
USE_CLOUDWATCH = int(os.environ['USE_CLOUDWATCH']) == 1
AWS_LOG_CLIENT = None

if USE_CLOUDWATCH is True:

    if IS_EC2 is True:

        AWS_LOG_CLIENT = boto3.client(
            service_name='logs',
            region_name=os.environ['AWS_CLOUDWATCH_REGION_NAME'],
        )

    else:

        AWS_LOG_CLIENT = boto3.client(
            service_name='logs',
            aws_access_key_id=os.environ['AWS_CLOUDWATCH_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_CLOUDWATCH_SECRET_ACCESS_KEY'],
            region_name=os.environ['AWS_CLOUDWATCH_REGION_NAME'],
        )

    LOGGING['handlers'].update({
        'watchtower': {
            'level': 'ERROR',
            'class': 'watchtower.CloudWatchLogHandler',
            'boto3_client': AWS_LOG_CLIENT,
            'log_group': os.environ['AWS_CLOUDWATCH_LOG_GROUP'],
            #can use different stream_name for each environment if needed
            'stream_name': f'logs',
            'formatter': 'verbose',
        },
    })

    LOGGING['loggers'].update({
        #use empty key (i.e. unnamed) to process from all loggers
        #ultimately allows the capturing of Django-raised logs, besides self-raised logs
        '': {
            'handlers': ['watchtower'],
            'level': 'DEBUG',
            'propagate': False,
        },
    })

else:

    LOGGING['handlers'].update({
        'error_file': {
            #log only severity of ERROR and above
            'level': 'ERROR',
            'filename': 'error.log',
            #choose formatter
            'formatter': 'verbose',
            #intead of FileHandler, use RotatingFileHandler for log rotation
            #help manage large log files by splitting them after reaching a particular size
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
        },
    })

    #in AWS, using only CloudWatch is sufficient, as SSHing into certain services to read log files is not as easy
    #plus, it will slowly increase file storage over time, which is bad when not needed at all
    LOGGING['loggers'].update({
        #use empty key (i.e. unnamed) to process from all loggers
        #ultimately allows the capturing of Django-raised logs, besides self-raised logs
        '': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
    })


#if this doesn't work, check django_site in db
#currently not used, which would have default example.com
SITE_ID = 1


#custom user model
AUTH_USER_MODEL = 'voicewake.User'


USERNAME_MAX_LENGTH = 30


#where to find all frontend + backend static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


#session in seconds, default 2 weeks
#used when not calling set_expiry(x) explicitly
#will be referred to for creating new and renewing sessions
SESSION_COOKIE_AGE = 1209600    #2 weeks

#when False (default), session is only renewed when any of its dict values are added/updated/deleted
#when True, session is renewed when user opens/reopens pages
SESSION_SAVE_EVERY_REQUEST = True


#if you have issues with bootstrap, try this:
# CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
# CRISPY_TEMPLATE_PACK = 'bootstrap5'


ROOT_URLCONF = 'voicewake.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'voicewake/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'voicewake.context_processors.settings_values',
            ],
        },
    },
]

WSGI_APPLICATION = 'voicewake.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {  
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': int(os.environ['DB_PORT']),
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

USE_I18N = True


# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


#using '/' instead of new URL for '/home'
#'/' does not need to be specified at urlpatterns
#'' did not work

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'


#timezone management
#TIME_ZONE default is 'America/Chicago', which was the case here, causing templates to have UTC -5
#when USE_TZ=False, Django stores datetime as UTC, and you should remove TIME_ZONE
#when USE_TZ=True: create data at 23:00 MY (UTC +8) --> stores as 23:00+08 --> template shows 15:00
USE_TZ = True
TIME_ZONE = 'UTC'

#DRF
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        'rest_framework.permissions.IsAdminUser',
    ],
}


ASGI_APPLICATION = 'voicewake.asgi.application'


#channel layers are optional, for app-to-app communication, e.g. real-time
#when testing, InMemoryChannelLayer is sufficient
#on deploy, must use Redis, as InMemoryChannelLayer is sub-optimal
CHANNEL_LAYERS = {}


#lockdown to keep site private
#if-else for LOCKDOWN_PASSWORDS is better than always '' for default, i.e. when in lockdown but accidentally no password
LOCKDOWN_ENABLED = int(os.environ.get('LOCKDOWN_ENABLED', 0)) == 1
LOCKDOWN_PASSWORDS = ('',) if LOCKDOWN_ENABLED == 0 else (os.environ['LOCKDOWN_PASSWORD'],)


#REDIS CACHE
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ['REDIS_ENDPOINT'] + "/1",    #/1 is database number
        "KEY_PREFIX": "voicewake",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}


#how long the audio clip processing updates should stay on Redis
REDIS_AUDIO_CLIP_PROCESSING_CACHE_EXPIRY_S = int(
    os.environ.get('REDIS_AUDIO_CLIP_PROCESSING_CACHE_EXPIRY_S', 691200)
)


#how long from last sync to db before new sync is needed
REDIS_AUDIO_CLIP_PROCESSING_CACHE_LAST_SYNC_FROM_DB_MIN_S = int(
    os.environ.get('REDIS_AUDIO_CLIP_PROCESSING_CACHE_LAST_SYNC_FROM_DB_MIN_S', 600)
)


#if file uploaded to Django server is below this, store in memory, else disk
#not relevant for S3 presigned POST URL
FILE_UPLOAD_MAX_MEMORY_SIZE = 5000000   #4.77mb


#UPLOADS
#some are in bytes
    #x/(1024*1024)
#file types
    #check VRecorder.vue
    #for S3 presigned POST URL, you can set the upload key's file type
        #at bucket, you can specify allowed extensions, e.g. ".../*.mp3"
        #however, the file type that end-user has, cannot be enforced, e.g. ".wav" uploading to ".mp3" key
AUDIO_CLIP_UNPROCESSED_FILE_EXTENSIONS = ['webm',]
AUDIO_CLIP_UNPROCESSED_EXPIRY_S = 3600  #1 hour
AUDIO_CLIP_PROCESSING_MAX_ATTEMPTS = 5


GENERAL_ROW_QUANTITY_PER_PAGE = 20


#EVENT
EVENT_CREATE_DAILY_LIMIT = 4      #compares from 00:00:00 UTC
EVENT_REPLY_DAILY_LIMIT = 8       #compares from 00:00:00 UTC
EVENT_REPLY_CHOICE_MAX_DURATION_S = 1200      #20 mins, when locked but is_replying=False
EVENT_REPLY_MAX_DURATION_S = 3600       #60 mins, for is_replying=True/False, and processing must be done strictly before this is reached
EVENT_QUANTITY_PER_PAGE = 10
#this must be balanced between "give older unreplied events a chance" and "new events get replied fast enough"
EVENT_INCOMPLETE_QUEUE_MAX_AGE_S = 302400   #3 days 12 hours


#EMAIL
#ports 465 (SSL), 587 (TLS, recommended)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ['AWS_SES_HOST']
EMAIL_HOST_USER = os.environ['AWS_SES_SMTP_USER_NAME']
EMAIL_HOST_PASSWORD = os.environ['AWS_SES_SMTP_PASSWORD']
DEFAULT_FROM_EMAIL = os.environ['AWS_SES_FROM_EMAIL']
EMAIL_USE_TLS = True
EMAIL_PORT = 587


#TOTP token arguments
#key minimum 120 bits, recommended 160 bits
#1 byte is 8 bits, so therefore minimum 15 bytes, recommended 20 bytes
TOTP_KEY_BYTE_SIZE = 20         #to pass into secrets.token_bytes(int) for creating totp_key
TOTP_NUMBER_OF_DIGITS = 6       #digits in OTP
TOTP_VALIDITY_S = 120     #seconds until expiry, a.k.a. steps
TOTP_TOLERANCE_S = 60    #allow early/late by x seconds until truly not allowed


#UserOTP-related arguments
#we make max values harder to reach but more punishing
OTP_CREATION_TIMEOUT_S = 30            #for each resend, before max is reached
OTP_MAX_CREATIONS = 4                       #max resends
OTP_MAX_CREATIONS_TIMEOUT_S = 600           #10 minutes
OTP_MAX_ATTEMPTS = 8                        #times someone can try before being timed out
OTP_MAX_ATTEMPTS_TIMEOUT_S = 1800           #30 minutes


#values used to evaluate audio_clip_reports and banning the audio_clips
#keeping it simple
BAN_AUDIO_CLIP_LIKE_RATIO = 0.25   #0 to 1
BAN_AUDIO_CLIP_DISLIKE_COUNT = 100
BAN_AUDIO_CLIP_MIN_AGE_S = 1800    #30 minutes
CRONJOB_BAN_AUDIO_CLIP_QUANTITY_LIMIT = 100
#ban duration limit done via community dislikes at cronjob
CRONJOB_AUDIO_CLIP_MAX_BAN_DAYS = 4
#ban duration limit done via admin manually banning
ADMIN_AUDIO_CLIP_BASE_BAN_DAYS = 5 #this ** ban_count
ADMIN_AUDIO_CLIP_MAX_BAN_DAYS = 1830 #366 days * 5, i.e. 5 years


#USER LIMITS
#for less important things that also gets all records
#or for things that just make sense when most reasonable cases would not exceed x amount
USER_BLOCKS_LIMIT = 200
USER_FOLLOWS_LIMIT = 400


#CACHE
CACHE_AUDIO_CLIP_TONE_AGE_S = 1209600  #2 weeks


#UNREGISTERED USERS
UNREGISTERED_USERS_MAX_INACTIVE_DURATION_S = 172800 #2 days
UNREGISTERED_USERS_DELETE_LIMIT = 100


#PERFORMANCE
BULK_CREATE_BATCH_SIZE = int(os.environ.get('BULK_CREATE_BATCH_SIZE', 100))
BULK_UPDATE_BATCH_SIZE = int(os.environ.get('BULK_UPDATE_BATCH_SIZE', 100))


#CELERY
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BROKER_URL = os.environ['REDIS_ENDPOINT']
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TIME_LIMIT = 2 * 60
#try connection to broker (Redis in this case) if it fails
#this is also to make "CPendingDeprecationWarning - broker_connection_retry" go away for Celery 6.0+
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
#tell Celery where to find @shared_task functions
#docs didn't show CELERY_IMPORTS, but code failed without it
CELERY_IMPORTS = ("voicewake.tasks", "voicewake.cronjobs",)


#CELERY BEAT
CRONJOB_DEFAULT_ROW_LIMIT = 100
CELERY_BEAT_HEALTHCHECK_CACHE_KEY = 'celery_beat_healthcheck_key'
#if you have args to pass, specify "'args': (param1, param2)"
CELERY_BEAT_SCHEDULE = {
    'cronjob_prepare_celery_beat_healthcheck': {
        'task': 'voicewake.cronjobs.cronjob_prepare_celery_beat_healthcheck',
        'schedule': (60),  #set cache key every 1 minute, check every 1 minute at healthcheck
        'options': {
            'expires': 30,    #30 seconds
        },
        'args': (120,), #cache timeout, 2 minutes, which if healthcheck cannot find cache key, means overdue
    },
    'cronjob_ban_audio_clips': {
        'task': 'voicewake.cronjobs.cronjob_ban_audio_clips',
        'schedule': (60 * 60),  #1 hour
        'options': {
            'expires': 30,    #30 seconds
        },
    },
    'cronjob_delete_event_reply_queue__not_replying__overdue': {
        'task': 'voicewake.cronjobs.cronjob_delete_event_reply_queue__not_replying__overdue',
        'schedule': (30 * 60),  #30 minutes
        'options': {
            'expires': 30,    #30 seconds
        },
    },
    'cronjob_delete_event_reply_queue__is_replying__delete_audio_clip__overdue': {
        'task': 'voicewake.cronjobs.cronjob_delete_event_reply_queue__is_replying__delete_audio_clip__overdue',
        'schedule': (30 * 60),  #30 minutes
        'options': {
            'expires': 30,    #30 seconds
        },
    },
    'cronjob_handle_originator_processing_overdue': {
        'task': 'voicewake.cronjobs.cronjob_handle_originator_processing_overdue',
        'schedule': (30 * 60),  #30 minutes
        'options': {
            'expires': 30,    #30 seconds
        },
    },
    'cronjob_delete_unregistered_users': {
        'task': 'voicewake.cronjobs.cronjob_delete_unregistered_users',
        'schedule': (12 * 60 * 60),  #12 hours
        'options': {
            'expires': 30,    #30 seconds
        },
    },
}






