from config.env import env
import logging

# Get an instance of a logger
logger = logging.getLogger("myapp")

EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = int(env("EMAIL_PORT"))
EMAIL_USE_TLS = env("EMAIL_USE_TLS") == "True"
EMAIL_USE_SSL = env("EMAIL_USE_SSL") == "True"
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_DEBUG = True  # This will log SMTP communication
