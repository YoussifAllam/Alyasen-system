from django.contrib import admin
from .models import base_project_models, rent_projects_models
from unfold.admin import ModelAdmin, StackedInline


@admin.register(base_project_models.BaseProject)
class ProjectsClass(ModelAdmin):
    list_display = (
        "id",
        "name",
    )


class RentProjectContractsInline(
    StackedInline
):  # Changed class name to indicate it's an inline
    model = rent_projects_models.RentProjectContracts
    extra = 1  # Number of empty forms to display
    fields = ("project", "contract")


@admin.register(rent_projects_models.RentProjects)
class RentProjectsClass(ModelAdmin):
    list_display = ("id",)

    inlines = [RentProjectContractsInline]
