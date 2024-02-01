from django.conf import settings


def settings_values(request):

    return {
        'STATIC_CACHE_BUST_VERSION': settings.STATIC_CACHE_BUST_VERSION,
    }