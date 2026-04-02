from django.apps import AppConfig


class CampaineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.Campaine"

    def ready(self):
        import apps.Campaine.signals  # noqa
