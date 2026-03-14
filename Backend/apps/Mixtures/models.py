from django.db import models
from django.utils.timezone import now

from apps.Material_Warehouse.models import MaterialWarehouse


class Mixtures(models.Model):
    name = models.CharField(max_length=50)
    materials_used_cost = models.FloatField(default=0)
    manufacturing_cost = models.FloatField(default=0)
    profit = models.FloatField(default=0)
    selling_price = models.FloatField(default=0)
    created_date = models.DateField(default=now)

    class Meta:
        db_table = "Mixtures"
        indexes = [
            models.Index(fields=["name"]),
        ]
        ordering = ["-created_date"]
        verbose_name = "Mixture"
        verbose_name_plural = "Mixtures"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.selling_price = self.manufacturing_cost + self.materials_used_cost + self.profit
        super().save(*args, **kwargs)


class MixtureMaterial(models.Model):
    mixture_fk = models.ForeignKey(Mixtures, on_delete=models.CASCADE, related_name="Mixture_Materials")
    material_fk = models.ForeignKey(MaterialWarehouse, on_delete=models.CASCADE)
    quantity_used = models.FloatField()

    class Meta:
        db_table = "MixtureMaterial"
        verbose_name = "Mixture Material"
        verbose_name_plural = "Mixture Materials"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Trigger the celery task to recalculate materials cost
        from .tasks.celery_tasks import calculate_mixture_materials_cost

        calculate_mixture_materials_cost.delay(self.mixture_fk.id)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        # Trigger recalculation after deletion
        from .tasks.celery_tasks import calculate_mixture_materials_cost

        calculate_mixture_materials_cost.delay(self.mixture_fk.id)
