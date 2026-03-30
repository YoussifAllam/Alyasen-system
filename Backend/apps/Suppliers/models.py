from django.db import models
from django.utils.timezone import now

from apps.Projects.models import BaseProject


class Supplier(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    total_amount_due = models.FloatField(default=0)
    total_amount_payable = models.FloatField(
        default=0, help_text="Remaining amount to supllier"
    )
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


class SupplierProjectBalance(models.Model):
    supplier_fk = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    project_fk = models.ForeignKey(BaseProject, on_delete=models.CASCADE)
    total = models.FloatField()
    paid = models.FloatField(default=0)
    remining = models.FloatField(default=0)

    class Meta:
        db_table = "supplier_project_balance"
        indexes = [
            models.Index(fields=["supplier_fk"]),
            models.Index(fields=["project_fk"]),
        ]
        verbose_name = "Supplier Project Balance"
        verbose_name_plural = "Supplier Project Balance"


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
