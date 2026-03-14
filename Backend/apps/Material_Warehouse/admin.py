from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


@admin.register(models.MaterialWarehouse)
class TransactionsLogClass(ModelAdmin):
    list_display = ("material_name",)
