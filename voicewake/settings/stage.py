from .common import *


DEBUG = False


#set these to True to avoid transmitting these over HTTP accidentally
#must already have redirect to HTTPS
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True


INSTALLED_APPS = ["storages"] + INSTALLED_APPS


#hide DRF UI in production, for aesthetic reasons
REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ]
})


STATICFILES_LOCATION = 'static/stage'
MEDIAFILES_LOCATION = 'media/stage'
AWS_S3_CUSTOM_DOMAIN = os.environ['AWS_S3_CUSTOM_DOMAIN']
AWS_S3_STATIC_BUCKET_NAME = os.environ['AWS_S3_STATIC_BUCKET_NAME']


BASE_S3_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/'
MEDIA_ROOT = f'https://{AWS_S3_CUSTOM_DOMAIN}/{MEDIAFILES_LOCATION}/'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATICFILES_LOCATION}/'
STATIC_ROOT = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATICFILES_LOCATION}/'


#for EC2 <--> S3, if EC2 has IAM role assigned, set these None to let boto auto-search for IAM role credentials at EC2
#otherwise, get these by creating access key for IAM user
AWS_S3_ACCESS_KEY_ID = None
AWS_S3_SECRET_ACCESS_KEY = None
if (
    'AWS_S3_ACCESS_KEY_ID' in os.environ and
    os.environ['AWS_S3_ACCESS_KEY_ID'] != '' and
    'AWS_S3_SECRET_ACCESS_KEY' in os.environ and
    os.environ['AWS_S3_SECRET_ACCESS_KEY'] != ''
):
    AWS_S3_ACCESS_KEY_ID = os.environ['AWS_S3_ACCESS_KEY_ID']
    AWS_S3_SECRET_ACCESS_KEY = os.environ['AWS_S3_SECRET_ACCESS_KEY']


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
            'region_name': os.environ['AWS_S3_REGION_NAME'],
            'object_parameters': {"CacheControl": "max-age=172800"}, #2 days
            'file_overwrite': True, #default True
            'location': STATICFILES_LOCATION, #folder name from S3 bucket root
        },
    },
}
#mistakes
    #OPTIONS must be at STORAGES.staticfiles.OPTIONS, not STORAGES.OPTIONS
        #will fail silently and defaults will be used