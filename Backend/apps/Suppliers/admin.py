from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


@admin.register(models.ProjectPayment)
class ProjectPaymentClass(ModelAdmin):
    list_display = ("payment_amount",)


@admin.register(models.SupplierProjectBalance)
class SupplierProjectBalanceClass(ModelAdmin):
    list_display = ("id",)


@admin.register(models.Supplier)
class SupplierClass(ModelAdmin):
    list_display = ("id",)
