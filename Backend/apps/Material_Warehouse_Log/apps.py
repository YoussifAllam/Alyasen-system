from django.apps import AppConfig


class Material_Warehouse_LogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.Material_Warehouse_Log"

    def ready(self):
        import apps.Material_Warehouse_Log.signals  # noqa
