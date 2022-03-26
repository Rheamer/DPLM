
import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from django.core.asgi import get_asgi_application
from devs.async_views import AsyncReadView
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dplmhub.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # WebSocket chat handler
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path(r'action/read/<str:clientID>', AsyncReadView.as_asgi(), name='wstream'),
        ])
    ),
})
