"""
ASGI config for fuckyou project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from django.core.asgi import get_asgi_application
from devs.views import AsyncStreamViewConsumer
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dplmhub.settings')


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # WebSocket chat handler
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path(r'action/stream/<str:clientID>', AsyncStreamViewConsumer.as_asgi(), name='wstream'),
        ])
    ),
})
