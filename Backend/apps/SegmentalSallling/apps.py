from django.apps import AppConfig


class SegmentalSalllingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.SegmentalSallling"

    def ready(self):
        from . import signals  # noqa
