from django.apps import AppConfig


class CompanyAssetsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.CompanyAssets"

    def ready(self):
        import apps.CompanyAssets.signals  # noqa
