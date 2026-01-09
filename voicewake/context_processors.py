from django.conf import settings
import os

def settings_values(request):

    if settings.DEBUG is True:

        return {
            'STATIC_CACHE_BUST_URL_APPEND': settings.STATIC_CACHE_BUST_URL_APPEND,
            'DEBUG': settings.DEBUG,
            'HOST': request.get_host().split(":")[0],
            'VITE_PORT': os.environ['VITE_PORT'],
        }

    else:

        return {
            'STATIC_CACHE_BUST_URL_APPEND': settings.STATIC_CACHE_BUST_URL_APPEND,
            'DEBUG': settings.DEBUG,
        }