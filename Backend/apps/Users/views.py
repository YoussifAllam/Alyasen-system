from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, parser_classes
from django.contrib.auth.hashers import make_password
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import UserSerializer
from rest_framework.request import Request

User = get_user_model()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request: Request) -> Response:
    user = UserSerializer(request.user, many=False)
    return Response(user.data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_user(request: Request) -> Response:
    user = request.user
    data = request.data

    user.first_name = data.get("first_name", user.first_name)
    user.last_name = data.get("last_name", user.last_name)

    user.username = data.get("username", user.username)

    if "password" in data and data["password"] != "":
        user.password = make_password(data["password"])

    # Check if 'profile_picture' is present in the request data
    if "profile_picture" in request.data:
        user.profile_picture = request.data["profile_picture"]

    if not user.created_Date:
        user.created_Date = timezone.now()

    user.save()
    serializer = UserSerializer(user, many=False)
    return Response(serializer.data)
