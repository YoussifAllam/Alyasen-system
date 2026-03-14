from django.db import models


class MaterialWarehouse(models.Model):
    material_name = models.CharField(max_length=100)
    quantity_in_unit = models.FloatField()
    unit = models.CharField(max_length=20)
    buy_price_per_unit = models.FloatField()

    class Meta:
        db_table = "MaterialWarehouse"
        indexes = [
            models.Index(fields=["material_name"]),
        ]
        verbose_name = "Material Warehouse "
        verbose_name_plural = "Material Warehouse "

    def __str__(self):
        return self.material_name
