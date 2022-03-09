"""
ASGI config for fuckyou project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import imp
import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path, include, path
from django.core.asgi import get_asgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dplmhub.settings')

from devs.views import StreamViewConsumer

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # WebSocket chat handler
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path(r'action/stream/<str:clientID>',StreamViewConsumer.as_asgi(), name = 'wstream'),
        ])
    ),
})
