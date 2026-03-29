from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


@admin.register(models.QuotationsAttachments)
class TransactionsLogClass(ModelAdmin):
    list_display = ("id",)
