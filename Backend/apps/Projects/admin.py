from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


@admin.register(models.Projects)
class ProjectsClass(ModelAdmin):
    list_display = (
        "name",
        "project_type",
        "project_status",
    )
