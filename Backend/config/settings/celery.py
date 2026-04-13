from __future__ import absolute_import, unicode_literals
from config.env import env
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

CELERY_BROKER_URL = env("REDIS_URL", default="amqp://guest:guest@localhost//")
CELERY_RESULT_BACKEND = env("REDIS_URL")

CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = "Africa/Cairo"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

app.conf.beat_schedule = {
    "check-check-cleared-notifications": {
        "task": "apps.Clients.Tasks.celery_tasks.check_check_cleared_notifications",
        "schedule": crontab(hour=12, minute=00),
        "options": {
            "expires": 3600,
        },
    },
    "check-insurance-tax-deadline": {
        "task": "apps.Projects.tasks.celery_tasks.check_insurance_tax_deadline",
        "schedule": crontab(hour=0, minute=0),
        "options": {
            "expires": 3600,
        },
    },
}


CELERY_IMPORTS = (
    #     "apps.TransactionsLog.tasks.celery_tasks",
    #     "apps.Suppliers.tasks.celery_tasks",
    #     "apps.Mixtures.tasks.celery_tasks",
    #     "apps.Clients.Tasks.celery_tasks",
)
