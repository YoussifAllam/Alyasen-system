from random import randint
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
)
from django.contrib.auth import login as django_login
from rest_framework.request import Request
from typing import TypedDict, Tuple, Optional
from datetime import timedelta, datetime

from apps.Users.models import User

from . import celery_tasks
from ..serializers import OutputSerializers
from .. import constant
from ..db_queries import selectors

current_site = constant.current_site


# Custom types
class TokenData(TypedDict):
    refresh: str
    access: str


class ApiResponse(TypedDict):
    detail: str


ResponseTuple = Tuple[dict, int]

# Constants
OTP_EXPIRY_MINUTES = 15
OTP_MIN = 1000
OTP_MAX = 9999
USER_TYPE_INVESTOR = "Investor"
USER_TYPE_CUSTOMER = "Customer"


def send_otp_to_user_email(user: User) -> TokenData:
    """Send OTP to user's email and return JWT tokens."""
    generate_and_save_otp(user)

    subject = f"Your verification OTP on {current_site}"
    send_otp_email(user, subject)

    return generate_token_for_user(user)


def is_otp_valid(otp_created_at: Optional[datetime]) -> bool:
    """Check if OTP is still valid based on creation time."""
    if not otp_created_at:
        return False
    expiration_time = otp_created_at + timedelta(minutes=OTP_EXPIRY_MINUTES)
    return timezone.now() <= expiration_time


def confirm_email_using_otp(request: Request) -> ResponseTuple:
    """Confirm user's email using provided OTP."""
    if not request.user.is_authenticated:
        return ({"message": "User is not authenticated"}, HTTP_401_UNAUTHORIZED)

    otp = request.data.get("otp")
    if not otp:
        return {"detail": "Missing OTP."}, HTTP_400_BAD_REQUEST

    user = request.user
    if user.email_verified:
        return {"detail": "Email already confirmed."}, HTTP_400_BAD_REQUEST

    if not otp.isdigit() or not (user.otp == int(otp) and is_otp_valid(user.otp_created_at)):
        return {"detail": "Invalid or expired OTP."}, HTTP_400_BAD_REQUEST

    user.email_verified = True
    user.save()
    return {"detail": "Email confirmed successfully."}, HTTP_200_OK


def send_reset_otp(request: Request) -> ResponseTuple:
    """Send reset password OTP to user's email."""
    if not request.user.is_authenticated:
        return ({"message": "User is not authenticated"}, HTTP_401_UNAUTHORIZED)

    user = request.user
    generate_and_save_otp(user)

    subject = f"Your reset OTP on {current_site}"
    send_otp_email(user, subject)

    return {"detail": "Reset OTP sent successfully."}, HTTP_200_OK


def login(request: Request) -> ResponseTuple:
    """Authenticate user and return tokens."""
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return {"message": "Email or Password missing"}, HTTP_400_BAD_REQUEST

    user = selectors.get_user_by_email(email)

    if not user.check_password(password):
        return {"message": "Invalid credentials"}, HTTP_401_UNAUTHORIZED

    if not user.is_active:
        return {"message": "Account deactivated"}, HTTP_403_FORBIDDEN

    if not user.email_verified:
        return {"user_id": user.uuid, "message": "Email not verified"}, HTTP_403_FORBIDDEN

    tokens = generate_token_for_user(user)
    django_login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    return {"user": OutputSerializers.LoginUserSerializer(user).data, "tokens": tokens}, HTTP_200_OK


def choose_user_type(request: Request) -> ResponseTuple:
    """Update user type."""
    user_type = request.data.get("user_type")

    if user_type not in [USER_TYPE_INVESTOR, USER_TYPE_CUSTOMER]:
        return {
            "error": f"Invalid user type. Choose {USER_TYPE_INVESTOR} or {USER_TYPE_CUSTOMER}"
        }, HTTP_400_BAD_REQUEST

    user = request.user
    user.user_type = user_type
    user.save()
    if user_type == USER_TYPE_INVESTOR:
        celery_tasks.send_email_to_admin(user.id)
    return {"message": "User type updated successfully"}, HTTP_200_OK


def generate_token_for_user(user: User) -> TokenData:
    """Generate JWT tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }


def generate_and_save_otp(user: User) -> int:
    """Generate OTP and save it to user model."""
    otp = randint(OTP_MIN, OTP_MAX)
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.save()
    return otp


def send_otp_email(user: User, subject: str) -> None:
    """Send OTP email to user."""
    html_message = constant.create_otp_template(f"{user.first_name} {user.last_name}", user.otp, user.email)
    celery_tasks.send_email_task.delay(user.id, subject, html_message)
