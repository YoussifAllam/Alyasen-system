from rest_framework.serializers import ModelSerializer
from apps.Users.models import User


class LoginUserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("user_type", "email_verified")
