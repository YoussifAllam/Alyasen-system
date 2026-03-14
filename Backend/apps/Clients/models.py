from django.db import models
from django.utils.timezone import now

from apps.Material_Warehouse.models import MaterialWarehouse

class Client(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    total_balance_owed_to_us = models.FloatField(default=0, help_text="Amount client owes to company")
    total_remaining_balance_owed_to_us = models.FloatField(default=0, help_text="Remaining amount to us")
    total_paid_amount = models.FloatField(default=0)
    profile_picture = models.ImageField(default="default.webp", upload_to="clients/")

    class Meta:
        db_table = "clients"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["phone"]),
        ]
        verbose_name = "Client"
        verbose_name_plural = "Clients"

    def __str__(self):
        return self.name


class ClientInvoice(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    invoice_number = models.AutoField(primary_key=True)
    invoice_date = models.DateField(default=now)
    invoice_total_amount = models.FloatField(default=0)
    total_amount_payable = models.FloatField(default=0, help_text="Remaining amount to invoice")
    total_paid_amount = models.FloatField(default=0)
    notes = models.TextField(blank=True, null=True)
    is_moved_to_warehouse = models.BooleanField(default=False)

    class Meta:
        db_table = "client_invoices"
        indexes = [
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["client", "invoice_date"]),
        ]
        verbose_name = "Client Invoice"
        verbose_name_plural = "Client Invoices"
        ordering = ["-invoice_date"]

    def __str__(self):
        return f"{self.invoice_number} - {self.client.name}"


class InvoiceMaterials(models.Model):
    invoice = models.ForeignKey(ClientInvoice, on_delete=models.CASCADE, related_name="materials")
    material = models.ForeignKey(MaterialWarehouse, on_delete=models.CASCADE)
    quantity_in_unit = models.FloatField()

    class Meta:
        indexes = [
            models.Index(fields=["invoice", "material"]),
        ]
        verbose_name = "Invoice Material"
        verbose_name_plural = "Invoice Materials"
        constraints = [models.UniqueConstraint(fields=["invoice", "material"], name="unique_client_invoice_material")]



class InvoicePayment(models.Model):
    client_fk = models.ForeignKey(Client, on_delete=models.CASCADE)
    payment_amount = models.FloatField()
    payment_date = models.DateField(default=now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "ClientPayments"
        indexes = [
            models.Index(fields=["client_fk"]),
            models.Index(fields=["payment_date"]),
        ]
        verbose_name = "Client Payments"
        verbose_name_plural = "Client Payments"
