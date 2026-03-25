from django.contrib import admin
from .models import base_project_models
from unfold.admin import ModelAdmin


@admin.register(base_project_models.BaseProject)
class ProjectsClass(ModelAdmin):
    list_display = ("name",)
