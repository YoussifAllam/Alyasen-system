from django.db import models
from django.utils.timezone import now

from apps.Material_Warehouse.models import MaterialWarehouse


class Invoice(models.Model):
    invoice_number = models.AutoField(primary_key=True)
    invoice_date = models.DateField(default=now)
    invoice_total_amount = models.FloatField(default=0)
    notes = models.TextField(blank=True, null=True)
    is_moved_to_warehouse = models.BooleanField(default=False)

    class Meta:
        db_table = "Segmental_invoices"
        indexes = [
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["invoice_date"]),
        ]
        ordering = ["-invoice_date"]

    def __str__(self):
        return f"{self.invoice_number}"


class SegmentalInvoiceMaterials(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="materials")
    material = models.ForeignKey(MaterialWarehouse, on_delete=models.CASCADE)
    quantity_in_unit = models.FloatField()

    class Meta:
        db_table = "segmental_invoice_material"
        indexes = [
            models.Index(fields=["invoice", "material"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["invoice", "material"], name="unique_segmental_invoice_material")
        ]


class SegmentalInvoicePayment(models.Model):
    payment_amount = models.FloatField()
    payment_date = models.DateField(default=now)

    class Meta:
        indexes = [
            models.Index(fields=["payment_date"]),
        ]
