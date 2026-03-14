from apps.Users.models import User
from rest_framework.exceptions import NotFound, ValidationError


def get_user_by_uuid(uuid: str) -> User:
    try:
        return User.objects.get(uuid=uuid)
    except User.DoesNotExist:
        raise NotFound("User not found")


def get_user_by_email(email: str) -> User:
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        raise NotFound("لا يوجد حساب بهذا البريد")


def get_user_by_token(token: str) -> User:
    try:
        return User.objects.get(profile__reset_password_token=token)
    except User.DoesNotExist:
        raise NotFound("User not found")
