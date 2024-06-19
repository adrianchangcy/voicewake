"""
ASGI config for voicewake project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack
    #AuthMiddlewareStack includes AuthMiddleware -reqs-> SessionMiddleware -reqs-> CookieMiddleware (hence all 3)

# import voicewake.websocket_routing

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'https': get_asgi_application(),
    # 'websocket': AuthMiddlewareStack(
    #     URLRouter(
    #         voicewake.websocket_routing.websocket_urlpatterns
    #     )
    # )
})
