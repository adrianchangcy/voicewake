from django.urls import re_path
from . import websocket_consumers

websocket_urlpatterns = [
    re_path(r'ws/socket-server', websocket_consumers.ChatConsumer.as_asgi()),
]