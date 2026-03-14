from django.apps import AppConfig


class ExpensesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.Expenses"

    def ready(self):
        import apps.Expenses.signals  # noqa
