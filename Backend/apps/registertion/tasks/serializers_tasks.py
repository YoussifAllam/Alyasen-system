import re
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from random import randint
from apps.Users.models import User


def validate_email(value, User: User):
    if User.objects.filter(email=value).exists():
        raise DjangoValidationError("Email is already registered.")
    return value


def validate_password_strength(value):
    if not re.search(r"\d", value):
        raise DjangoValidationError("Password must contain at least 1 digit.")

    # Check if the password contains at least one uppercase letter
    if not re.search(r"[A-Z]", value):
        raise DjangoValidationError("Password must contain at least 1 uppercase letter.")

    # Call Django's built-in password validators
    validate_password(value)
    return value


def generate_unique_username(first_name, last_name, User: User):
    base_username = re.sub(r"\s+", "_", f"{first_name}_{last_name}").lower()
    while True:
        random_number = randint(1000, 9999)
        unique_username = f"{base_username}_{random_number}"
        try:
            User.objects.get(username=unique_username)
        except User.DoesNotExist:
            return unique_username
