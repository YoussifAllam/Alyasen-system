from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


@admin.register(models.Client)
class ClientClass(ModelAdmin):
    list_display = ("name",)


@admin.register(models.ProjectPayment)
class ProjectPaymentClass(ModelAdmin):
    list_display = ("client_project_balance_fk", "payment_amount", "payment_date")


@admin.register(models.ClientProjectBalance)
class ClientProjectBalanceClass(ModelAdmin):
    list_display = ("client_fk", "project_fk", "campaine_fk", "project_type")
