from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import AppVersion


@admin.register(AppVersion)
class AppVersionAdmin(ModelAdmin):
    list_display = ("version", "setup_file", "notes", "updated_at")
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request):
        # Only allow adding if no instance exists yet
        if AppVersion.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting the singleton instance
        return False
