import os
from config.env import BASE_DIR


def skip_common_errors(record):
    """Skip 400, 404 and invalid HTTP_HOST errors"""
    if hasattr(record, "status_code") and record.status_code in [400, 404]:
        return False
    if hasattr(record, "msg") and isinstance(record.msg, str):
        if "Invalid HTTP_HOST header" in record.msg:
            return False
    return True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(message)s",
            "style": "%",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "filters": {
        "skip_common_errors": {
            "()": "django.utils.log.CallbackFilter",
            "callback": skip_common_errors,
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",  # Changed from FileHandler
            "filename": os.path.join(BASE_DIR, "LOGS/django.log"),
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "debug_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "LOGS/debug.log"),
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "cacheops_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "LOGS/cacheops.log"),
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
            "formatter": "verbose",
            "filters": ["skip_common_errors"],
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file", "mail_admins"],
            "level": "ERROR",
            "propagate": False,  # Changed to False to avoid duplicate logs
        },
        "django.request": {
            "handlers": ["file", "mail_admins"],  # Added file handler
            "level": "ERROR",
            "propagate": False,
        },
        "debug": {
            "handlers": ["console", "debug_file"],  # Use debug_file for INFO
            "level": "INFO",
            "propagate": False,
        },
        "cacheops": {
            "handlers": ["cacheops_file"],  # Use debug_file for DEBUG
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

DRF_API_LOGGER_METHODS = ["POST", "DELETE", "PUT", "PATCH"]
DRF_API_LOGGER_DATABASE = True
