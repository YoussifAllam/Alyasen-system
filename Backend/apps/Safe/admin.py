from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


@admin.register(models.SafeLogs)
class SafeClass(ModelAdmin):
    list_display = (
        "operation_type",
        "amount",
        "balance_after",
        "trnasaction",
        "date",
    )
