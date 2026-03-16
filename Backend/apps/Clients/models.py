from django.db import models
from django.utils.timezone import now


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


# class InvoicePayment(models.Model):
#     client_fk = models.ForeignKey(Client, on_delete=models.CASCADE)
#     payment_amount = models.FloatField()
#     payment_date = models.DateField(default=now)
#     notes = models.TextField(blank=True, null=True)

#     class Meta:
#         db_table = "ClientPayments"
#         indexes = [
#             models.Index(fields=["client_fk"]),
#             models.Index(fields=["payment_date"]),
#         ]
#         verbose_name = "Client Payments"
#         verbose_name_plural = "Client Payments"
