from django.contrib import admin
from .models import User, Profile
from unfold.admin import ModelAdmin, StackedInline


class ProfileAdmin(StackedInline):
    model = Profile
    extra = 1


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = (
        "email",
        "is_staff",
        "is_approvid",
        "user_type",
        "last_login",
        "email_verified",
        "created_Date",
    )

    list_filter = ("is_staff", "is_active", "groups", "email_verified", "user_type")

    list_editable = ("is_approvid",)

    search_fields = ("username", "email", "uuid")

    ordering = ("username",)
    inlines = [ProfileAdmin]


# admin.site.register(User, UserAdmin)
