from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    BooleanField,
    ImageField,
    ValidationError,
    EmailField,
)
from apps.Users.models import User, UserTypeChoice
from ..tasks import serializers_tasks
from ..db_queries import services


class SignUpSerializer(ModelSerializer):
    confirm_password = CharField(write_only=True, required=False)
    password = CharField(write_only=True, required=False)
    email = EmailField(required=True)
    user_type = CharField(required=True)

    class Meta:
        model = User
        fields = [
            "uuid",
            "name",
            "email",
            "password",
            "confirm_password",
            "email_verified",
            "user_type",
        ]
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            "email": {"required": True},
            "user_type": {"required": True},
        }

    def validate_email(self, value: str):
        return serializers_tasks.validate_email(value, User)

    def validate_password(self, value: str):
        return serializers_tasks.validate_password_strength(value)

    def validate_user_type(self, value: str):
        if value not in UserTypeChoice.values:
            print(value)
            raise ValidationError("Invalid user type.")
        return value

    def validate_confirm_password(self, value: str):
        if value != self.initial_data["password"]:
            raise ValidationError("Passwords do not match.")
        return value

    def create(self, validated_data: dict):
        return services.Create_user(validated_data)
