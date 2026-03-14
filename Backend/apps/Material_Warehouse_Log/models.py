from django.db import models
from django.utils.timezone import now


class MaterialWarehouseLog(models.Model):
    material_name = models.CharField(max_length=100)
    transaction = models.TextField()
    transaction_date = models.DateField(default=now)
    quantity_before = models.FloatField()
    quantity_after = models.FloatField()

    class Meta:
        db_table = "MaterialWarehouseLog"
        indexes = [
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["material_name"]),
            models.Index(fields=["material_name", "transaction_date"]),
        ]
        ordering = ["-transaction_date"]
        verbose_name = "Material Warehouse Log"
        verbose_name_plural = "Material Warehouse Log"

    def __str__(self):
        return self.material_name
