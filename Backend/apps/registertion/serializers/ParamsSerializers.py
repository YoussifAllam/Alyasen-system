from rest_framework.serializers import Serializer, CharField, EmailField
from rest_framework.exceptions import ValidationError
from ..tasks import serializers_tasks


class UpdateUserPasswordSerializer(Serializer):
    password = CharField(required=True)
    confirmPassword = CharField(required=True)

    # Validate new password strength
    def validate_confirmPassword(self, value):
        if not serializers_tasks.validate_password_strength(value):
            raise ValidationError("New password is too weak.")
        return value

    # Cross-field validation to check if new_password matches confirm_password
    def validate(self, data):
        new_password = data.get("password")
        confirm_password = data.get("confirmPassword")

        if new_password != confirm_password:
            raise ValidationError({"confirm_password": "New password and confirm password do not match."})
        return data


class EmailSerializer(Serializer):
    email = EmailField(required=True)
