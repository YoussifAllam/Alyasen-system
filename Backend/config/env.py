import environ  # ignore:E402
from django.core.exceptions import ImproperlyConfigured
from os.path import join
from typing import Type, Any
import enum
import os

env = environ.Env()

BASE_DIR = environ.Path(__file__) - 2
APPS_DIR = BASE_DIR.path(f"{BASE_DIR}/apps")

# Don't read .env from root directory since we use environment-specific files
# env.read_env(join(BASE_DIR, ".env"))

# Detect the environment
ENVIRONMENT = env.str("ENVIRONMENT")

# Load the corresponding environment file
env_file_path = join(BASE_DIR, f"ENV/.env.{ENVIRONMENT}")

if not os.path.exists(env_file_path):
    raise ImproperlyConfigured(f"Environment file '{env_file_path}' not found.")

env.read_env(env_file_path)


def env_to_enum(enum_cls: Type[enum.Enum], value: Any) -> enum.Enum:
    for x in enum_cls:
        if x.value == value:
            return x

    raise ImproperlyConfigured(f"Env value {repr(value)} could not be found in {repr(enum_cls)}")
