from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


@admin.register(models.InvoicePayment)
class InvoicePaymentClass(ModelAdmin):
    list_display = ("payment_amount",)
