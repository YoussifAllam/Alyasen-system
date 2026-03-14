from django.apps import AppConfig


class SuppliersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.Suppliers"

    def ready(self):
        import apps.Suppliers.signals  # noqa
