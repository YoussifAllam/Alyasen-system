from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


@admin.register(models.MaterialWarehouseLog)
class MaterialWarehouseLogClass(ModelAdmin):
    list_display = (
        "material_name",
        "transaction",
        "transaction_date",
        "quantity_before",
        "quantity_after",
    )
