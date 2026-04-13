from django.apps import AppConfig


class MaterialsSuppliersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.MaterialsSuppliers"

    def ready(self):
        import apps.MaterialsSuppliers.signals  # noqa
