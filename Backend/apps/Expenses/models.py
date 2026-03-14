from django.db import models
from django.utils.timezone import now


class Expenses(models.Model):
    transaction = models.TextField()
    permit_number = models.CharField(max_length=10, blank=True, null=True)
    amount = models.FloatField()
    created_date = models.DateField(default=now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "Expenses"
        indexes = [
            models.Index(fields=["created_date"]),
            models.Index(fields=["transaction"]),
            models.Index(fields=["transaction", "created_date"]),
        ]
        ordering = ["-created_date"]
        verbose_name = "Expenses"
        verbose_name_plural = "Expenses"

    def __str__(self):
        return self.transaction
