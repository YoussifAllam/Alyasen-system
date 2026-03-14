from django.apps import AppConfig


class MachinesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.Machines"

    def ready(self):
        import apps.Machines.signals  # noqa
