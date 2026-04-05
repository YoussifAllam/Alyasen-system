from django.db import models
from django.utils.timezone import now


# from apps.Clients.models import Client
from apps.Suppliers.models import Supplier
from apps.Projects.models import BaseProject


class Campaine(models.Model):
    name = models.CharField(max_length=150)
    client = models.ForeignKey(
        "Clients.Client", on_delete=models.CASCADE, related_name="campaigns", null=True
    )
    total_cost = models.FloatField(default=0)
    created_date = models.DateField(default=now)

    class Meta:
        db_table = "campaine"
        verbose_name = "Campaine"
        verbose_name_plural = "Campaines"

    def __str__(self):
        return f"{self.name} - {self.client.name}"


class CampaineItem(models.Model):
    campaine = models.ForeignKey(
        Campaine, on_delete=models.CASCADE, related_name="items"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="campaign_items"
    )
    project = models.ForeignKey(
        BaseProject, on_delete=models.CASCADE, related_name="campaign_items"
    )

    class Meta:
        db_table = "campaine_item"
        verbose_name = "Campaine Item"
        verbose_name_plural = "Campaine Items"

    def __str__(self):
        return f"{self.campaine.name} - {self.supplier.name} - {self.project.name}"
