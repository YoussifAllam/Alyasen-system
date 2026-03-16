from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


@admin.register(models.Client)
class ClientClass(ModelAdmin):
    list_display = ("name",)
