from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


@admin.register(models.SegmentalInvoicePayment)
class SegmentalInvoicePaymentClass(ModelAdmin):
    list_display = ("payment_amount",)


@admin.register(models.Invoice)
class InvoiceClass(ModelAdmin):
    list_display = ("invoice_number", "invoice_date")
