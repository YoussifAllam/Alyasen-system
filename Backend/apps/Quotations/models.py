from django.db import models
from django.utils.timezone import now


class Quotations(models.Model):
    client_name = models.CharField(max_length=50, blank=True, null=True)
    company_name = models.CharField(max_length=50, blank=True, null=True)
    price = models.FloatField()
    details = models.TextField()
    quotation_last_date = models.DateField(default=now)
    created_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Quotations"
        indexes = [
            models.Index(fields=["quotation_last_date"]),
            models.Index(fields=["client_name"]),
            models.Index(fields=["created_date"]),
        ]
        ordering = ["-quotation_last_date"]
        verbose_name = "Quotation"
        verbose_name_plural = "Quotations"

    def __str__(self):
        return self.client_name


class QuotationsAttachments(models.Model):
    quotation = models.ForeignKey(Quotations, on_delete=models.CASCADE)
    attachment = models.FileField(upload_to="quotations/%Y/%m/%d/")
