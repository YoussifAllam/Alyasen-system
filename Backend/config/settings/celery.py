from __future__ import absolute_import, unicode_literals
from config.env import env
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# app.conf.beat_schedule = {
#     "release-old-temporary-bookings": {
#         "task": "apps.Dresses.tasks.release_old_temporary_bookings",
#         "schedule": crontab(minute="*/5"),  # Adjust the schedule as needed
#     },
# }

CELERY_BROKER_URL = env("REDIS_URL", default="amqp://guest:guest@localhost//")
CELERY_RESULT_BACKEND = env("REDIS_URL")

CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = "UTC"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

CELERY_BEAT_SCHEDULE = {}

CELERY_IMPORTS = (
#     "apps.TransactionsLog.tasks.celery_tasks",
#     "apps.Suppliers.tasks.celery_tasks",
#     "apps.Mixtures.tasks.celery_tasks",
#     "apps.Clients.Tasks.celery_tasks",
)
