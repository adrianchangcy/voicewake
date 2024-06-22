from django.conf import settings
import os

def settings_values(request):

    if settings.DEBUG is True:

        return {
            'STATIC_CACHE_BUST_VERSION': settings.STATIC_CACHE_BUST_VERSION,
            'DEBUG': settings.DEBUG,
            'VITE_PORT': os.environ['VITE_PORT'],
            'HOST': request.get_host().split(":")[0],
        }

    else:

        return {
            'STATIC_CACHE_BUST_VERSION': settings.STATIC_CACHE_BUST_VERSION,
            'DEBUG': settings.DEBUG,
        }