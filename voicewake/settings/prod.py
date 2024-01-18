from .common import *


DEBUG = False


ALLOWED_HOSTS = ['voicewake.com']


#set these to True to avoid transmitting these over HTTP accidentally
#must already have redirect to HTTPS
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True



