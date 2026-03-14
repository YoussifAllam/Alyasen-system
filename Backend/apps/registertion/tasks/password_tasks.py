from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol, Tuple, TypeVar, Type

from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.serializers import BaseSerializer

from .. import constant
from ..db_queries import selectors
from ..serializers import ParamsSerializers
from . import celery_tasks, get_device_info_tasks
from apps.Users.models import User

ResponseType = Tuple[dict, int]
SerializerType = TypeVar("SerializerType", bound=BaseSerializer)


@dataclass
class DeviceInfo:
    operating_system: str
    browser_name: str


class EmailService(Protocol):
    """Added proper type hints and a Protocol for email service dependency injection."""

    def send_email(self, user_id: int, subject: str, message: str) -> None: ...  # noqa


class PasswordService:
    TOKEN_LENGTH = 40
    TOKEN_EXPIRY_MINUTES = 10

    def __init__(self, email_service: EmailService = celery_tasks):
        self.email_service = email_service

    def validate_password(self, user: User, password: str) -> bool:
        """Validate if provided password matches user's password."""
        return user.check_password(password)

    def create_reset_token(self, user: User) -> str:
        """Create and store password reset token for user."""
        token = get_random_string(self.TOKEN_LENGTH)
        expire_date = datetime.now() + timedelta(minutes=self.TOKEN_EXPIRY_MINUTES)

        user.profile.reset_password_token = token
        user.profile.reset_password_expire = expire_date
        user.profile.save(update_fields=["reset_password_token", "reset_password_expire"])

        return token

    def send_reset_password_email(self, request: Request) -> ResponseType:
        """Send password reset email to user."""
        self._validate_request(ParamsSerializers.EmailSerializer, request.data)

        email = request.data.get("email")
        user = selectors.get_user_by_email(email)
        token = self.create_reset_token(user)

        # Get device info tuple and convert to DeviceInfo
        operating_system, browser_name = get_device_info_tasks.get_device_info(request)
        device_info = DeviceInfo(operating_system=operating_system, browser_name=browser_name)

        reset_link = f"{constant.rest_password_url}?token={token}"

        self._send_reset_email(user, device_info, reset_link)

        return {"message": f"Password reset instructions sent to {email}"}, status.HTTP_200_OK

    def reset_password(self, request: Request, token: str) -> ResponseType:
        """Reset user's password using valid token."""
        self._validate_request(ParamsSerializers.UpdateUserPasswordSerializer, request.data)

        user = selectors.get_user_by_token(token)
        if not self._is_token_valid(user):
            return {"error": "Token has expired"}, status.HTTP_400_BAD_REQUEST

        self._update_password(user, request.data["password"])
        return {"message": "Password reset successful"}, status.HTTP_200_OK

    def _validate_request(self, serializer_class: Type[SerializerType], data: dict) -> None:
        """Validate request data using provided serializer."""
        serializer = serializer_class(data=data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

    def _is_token_valid(self, user: User) -> bool:
        """Check if reset token is still valid."""
        return user.profile.reset_password_expire.replace(tzinfo=None) >= datetime.now()

    def _update_password(self, user: User, new_password: str) -> None:
        """Update user's password and clear reset token."""
        user.password = make_password(new_password)
        user.profile.reset_password_token = ""
        user.profile.reset_password_expire = None

        user.profile.save(update_fields=["reset_password_token", "reset_password_expire"])
        user.save(update_fields=["password"])

    def _send_reset_email(self, user: User, device_info: DeviceInfo, reset_link: str) -> None:
        """Send password reset email to user."""
        subject = f"Password Reset Request - {constant.current_site}"

        html_message = constant.create_password_reset_template(
            user_name=f"{user.first_name} {user.last_name}",
            reset_link=reset_link,
            operating_system=device_info.operating_system,
            browser_name=device_info.browser_name,
        )

        self.email_service.send_email_task.delay(user.id, subject, html_message)


# Create singleton instance
password_service = PasswordService()


# Public interface
def check_user_password_is_correct(user: User, password: str) -> bool:
    return password_service.validate_password(user, password)


def send_rest_password_otp(request: Request) -> ResponseType:
    return password_service.send_reset_password_email(request)


def reset_password(request: Request, token: str) -> ResponseType:
    return password_service.reset_password(request, token)
