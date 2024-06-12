from django.conf import settings


def settings_values(request):

    if settings.DEBUG is True:

        return {
            'STATIC_CACHE_BUST_VERSION': settings.STATIC_CACHE_BUST_VERSION,
            'DEBUG': settings.DEBUG,
            #remove :xxxx port from host
            #can specify port at template to load local JS files at base.html
            'HOST': request.get_host().split(':')[0],
        }

    else:

        return {
            'STATIC_CACHE_BUST_VERSION': settings.STATIC_CACHE_BUST_VERSION,
            'DEBUG': settings.DEBUG,
        }