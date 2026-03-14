import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

# from channels.auth import AuthMiddlewareStack


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django")


django_application = get_asgi_application()


# Import after Django setup


# todo from apps.chat.routing import websocket_urlpatterns as chat_websocket_urlpatterns  # noqa
# todo from apps.Notifications.routing import websocket_urlpatterns as notification_websocket_urlpatterns  # noqa
# todo combined_websocket_patterns = chat_websocket_urlpatterns + notification_websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_application,
        #  "websocket": AuthMiddlewareStack(URLRouter(combined_websocket_patterns)),
    }
)
