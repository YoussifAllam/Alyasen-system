from config.env import env
from .base import *  # noqa

DEBUG = True

SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = [
    "*",
]

INSTALLED_APPS += [  # noqa
    "debug_toolbar",
]

MIDDLEWARE += [  # noqa
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]


DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
    "IS_RUNNING_TESTS": False,
}
