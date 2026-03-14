import os
from .base import *  # noqa
from config.env import env

# This is extremely "eye-poking",
# but we need it, if we want to ignore the debug toolbar in tests
# This is needed because of the way we setup Django Debug Toolbar.
# Since we import base settings, the entire setup will be done, before we have any chance to change.
# A different way of approaching this would be to have a separate set of env variables for tests.
# os.environ.setdefault("DEBUG_TOOLBAR_ENABLED", "False")


SECRET_KEY = env("SECRET_KEY")
BASE_URL = env("DJANGO_BASE_BACKEND_URL")
DEBUG = True


PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

AUTH_PASSWORD_VALIDATORS: list[dict[str, int]] = [  # type: ignore
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
