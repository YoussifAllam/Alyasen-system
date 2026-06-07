from django.db import models
from django.utils.timezone import now

from apps.Projects.models import BaseProject
from apps.Campaine.models import Campaine


class ProjectTypes(models.Choices):
    project = "project"
    campaine = "campaine"


class PaymentTypes(models.Choices):
    cash = "cash"
    visa = "visa"
    bank_transfer = "bank_transfer"
    check = "check"


class Client(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    total_balance_owed_to_us = models.FloatField(
        default=0, help_text="Amount client owes to company"
    )
    total_remaining_balance_owed_to_us = models.FloatField(
        default=0, help_text="Remaining amount to us"
    )
    total_paid_amount = models.FloatField(default=0)
    profile_picture = models.ImageField(
        default="clients/default.webp", upload_to="clients/"
    )

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


class ClientProjectBalance(models.Model):
    client_fk = models.ForeignKey(Client, on_delete=models.CASCADE)
    project_fk = models.ForeignKey(
        BaseProject, on_delete=models.CASCADE, null=True, blank=True
    )
    campaine_fk = models.ForeignKey(
        Campaine, on_delete=models.CASCADE, null=True, blank=True
    )
    project_type = models.CharField(
        max_length=20, choices=ProjectTypes.choices, default="campaine"
    )
    total = models.FloatField()
    paid = models.FloatField(default=0)
    remining = models.FloatField(default=0)
    created_date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "client_project_balance"
        indexes = [
            models.Index(fields=["client_fk"]),
            models.Index(fields=["project_fk"]),
            models.Index(fields=["campaine_fk"]),
        ]
        verbose_name = "Client Project Balance"
        verbose_name_plural = "Client Project Balance"

    @property
    def project_name(self):
        if self.project_type == "project" and self.project_fk:
            return self.project_fk.name
        elif self.project_type == "campaine" and self.campaine_fk:
            return self.campaine_fk.name
        return "N/A"


class ProjectPayment(models.Model):
    client_project_balance_fk = models.ForeignKey(
        ClientProjectBalance, on_delete=models.CASCADE, related_name="payments"
    )
    portal_invoice_number = models.CharField(max_length=50, null=True, blank=True)
    portal_invoice_file = models.FileField(upload_to="clients/invoices/", null=True)
    payment_amount = models.FloatField()
    payment_date = models.DateField(default=now)
    payment_type = models.CharField(
        max_length=20, choices=PaymentTypes.choices, default="cash"
    )
    check_cleared_date = models.DateField(null=True, blank=True)
    is_cleared = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["client_project_balance_fk"]),
            models.Index(fields=["payment_date"]),
        ]
        verbose_name = "Client Project Payment"
        verbose_name_plural = "Client Project Payment"
