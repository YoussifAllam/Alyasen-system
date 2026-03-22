from django.contrib import admin
from .models import Notification
from unfold.admin import ModelAdmin


@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ("title", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("title", "message")
