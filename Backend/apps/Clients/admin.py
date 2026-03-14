from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


@admin.register(models.Client)
class ClientClass(ModelAdmin):
    list_display = ("name",)


@admin.register(models.ClientInvoice)
class ClientInvoiceClass(ModelAdmin):
    list_display = ("invoice_number", "invoice_date")


@admin.register(models.InvoicePayment)
class InvoicePaymentClass(ModelAdmin):
    list_display = ("payment_amount",)


@admin.register(models.InvoiceMaterials)
class InvoiceMixturesClass(ModelAdmin):
    list_display = ("material",)
