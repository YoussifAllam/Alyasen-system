from os.path import join
from config.env import env, ENVIRONMENT, BASE_DIR

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent


if ENVIRONMENT == "TEST":
    DATABASES = {
        "default": {
            "ENGINE": env("TEST_DATABASE_ENGINE"),
            "NAME": env("TEST_DATABASE_NAME"),
            "USER": env("TEST_DATABASE_USER"),
            "PASSWORD": env("TEST_DATABASE_PASSWORD"),
            "HOST": env("TEST_DATABASE_HOST"),
            "PORT": env("TEST_DATABASE_PORT"),
            "OPTIONS": {
                "options": "-c search_path=public",
            },
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }
    }


elif ENVIRONMENT == "Production":
    DATABASES = {
        "default": {
            "ENGINE": env("PROD_DATABASE_ENGINE"),
            "NAME": env("PROD_DATABASE_NAME"),
            "USER": env("PROD_DATABASE_USER"),
            "PASSWORD": env("PROD_DATABASE_PASSWORD"),
            "HOST": env("PROD_DATABASE_HOST"),
            "PORT": env("PROD_DATABASE_PORT"),
            "OPTIONS": {
                "options": "-c search_path=public",
            },
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
        }
    }


else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": join(BASE_DIR, "db.sqlite3"),
        }
    }
