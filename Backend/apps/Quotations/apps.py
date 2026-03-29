from django.apps import AppConfig


class PaymentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.Quotations"

    def ready(self):
        import apps.Quotations.signals  # noqa
