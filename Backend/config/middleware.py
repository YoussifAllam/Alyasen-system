# config/middleware.py
from channels.db import database_sync_to_async
from jwt.exceptions import InvalidTokenError
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user_from_token(token):
    # Import inside the function to avoid premature access
    from apps import Users

    try:
        decoded_data = AccessToken(token)  # Decode the token
        user_id = decoded_data["user_id"]
        return Users.objects.get(id=user_id)
    except (InvalidTokenError, Users.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware:
    """Middleware to attach user to the WebSocket scope using JWT."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # Parse token from query string
        query_string = scope["query_string"].decode()
        params = dict(param.split("=") for param in query_string.split("&") if "=" in param)
        token = params.get("token", None)

        # Attach user to the scope
        scope["user"] = await get_user_from_token(token) if token else AnonymousUser()

        # Pass to the next layer
        return await self.inner(scope, receive, send)
