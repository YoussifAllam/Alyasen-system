from django.db import models
from django.utils.timezone import now


class Supplier(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    total_amount_due = models.FloatField(default=0)
    total_amount_payable = models.FloatField(default=0, help_text="Remaining amount to supllier")
    total_paid_amount = models.FloatField(default=0)
    profile_picture = models.ImageField(default="default.webp", upload_to="suppliers/")

    class Meta:
        db_table = "suppliers"
        indexes = [
            models.Index(fields=["name"]),
        ]
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"

    def __str__(self):
        return self.name


class SupplierInvoice(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    invoice_number = models.AutoField(primary_key=True)
    invoice_date = models.DateField(default=now)
    invoice_total_amount = models.FloatField(default=0)
    notes = models.TextField(blank=True, null=True)
    is_moved_to_warehouse = models.BooleanField(default=False)

    class Meta:
        db_table = "supplier_invoices"
        indexes = [
            models.Index(fields=["invoice_number"]),
            models.Index(fields=["supplier", "invoice_date"]),
        ]
        verbose_name = "Supplier Invoice"
        verbose_name_plural = "Supplier Invoices"
        ordering = ["-invoice_date"]

    def __str__(self):
        return f"{self.invoice_number} - {self.supplier.name}"


class InvoiceMaterial(models.Model):
    invoice = models.ForeignKey(SupplierInvoice, on_delete=models.CASCADE, related_name="materials")
    material_name = models.CharField(max_length=100)
    quantity_in_unit = models.FloatField()
    buy_price_per_unit = models.FloatField()
    unit = models.CharField(max_length=20)

    class Meta:
        db_table = "invoice_materials"
        indexes = [
            models.Index(fields=["invoice", "material_name"]),
        ]
        verbose_name = "Invoice Material"
        verbose_name_plural = "Invoice Materials"
        constraints = [
            models.UniqueConstraint(fields=["invoice", "material_name"], name="unique_invoice_material")
        ]


class InvoicePayment(models.Model):
    supplier_fk = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    payment_amount = models.FloatField()
    payment_date = models.DateField(default=now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "supplier_payments"
        indexes = [
            models.Index(fields=["supplier_fk"]),
            models.Index(fields=["payment_date"]),
        ]
        verbose_name = "Supplier Payment"
        verbose_name_plural = "Supplier Payment"
