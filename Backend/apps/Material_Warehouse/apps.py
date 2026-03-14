from django.apps import AppConfig


class Material_WarehouseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.Material_Warehouse"

    def ready(self):
        import apps.Material_Warehouse.signals  # noqa
