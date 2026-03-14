from django.apps import AppConfig


class SuppliersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.Workers"

    def ready(self):
        import apps.Workers.signals  # noqa
