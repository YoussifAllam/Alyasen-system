from .models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = (
            "uuid",
            "username",
            "first_name",
            "last_name",
            "email",
            "profile_picture",
            "is_staff",
            "is_superuser",
            "is_approvid",
            "user_type",
            "email_verified",
        )
