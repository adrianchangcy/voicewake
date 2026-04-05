from .common import *


DEBUG = False


#set these to True to avoid transmitting these over HTTP accidentally
#must already have redirect to HTTPS
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True


#allows us to upload to S3
INSTALLED_APPS = ["storages"] + INSTALLED_APPS


#hide DRF UI in production, for aesthetic reasons
REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ]
})


STATIC_AWS_S3_START_PATH = 'static/stage'
MEDIA_AWS_S3_START_PATH = 'media/stage'


MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
MEDIA_ROOT = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_AWS_S3_START_PATH}/'
STATIC_ROOT = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_AWS_S3_START_PATH}/'


#how long to cache at CDN or user browser before refetching from server
HTTP_CACHE_CONTROL_MAX_AGE = str(os.environ.get('HTTP_CACHE_CONTROL_MAX_AGE', 172800)) #2 days


#use this for Django >= 4.2
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            'access_key': AWS_S3_ACCESS_KEY_ID,
            'secret_key': AWS_S3_SECRET_ACCESS_KEY,
            'bucket_name': AWS_S3_STATIC_BUCKET_NAME,
            'custom_domain': AWS_S3_CUSTOM_DOMAIN,
            'region_name': AWS_S3_REGION_NAME,
            'object_parameters': {"CacheControl": f"max-age={HTTP_CACHE_CONTROL_MAX_AGE}"},
            'file_overwrite': True, #default True
            'location': STATIC_AWS_S3_START_PATH, #folder name from S3 bucket root
        },
    },
}
#mistakes
    #OPTIONS must be at STORAGES.staticfiles.OPTIONS, not STORAGES.OPTIONS
        #will fail silently and defaults will be used