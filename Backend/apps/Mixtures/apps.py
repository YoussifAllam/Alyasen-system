from django.apps import AppConfig


class PaymentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.Mixtures"

    def ready(self):
        import apps.Mixtures.signals  # noqa
