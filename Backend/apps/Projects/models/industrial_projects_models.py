from django.db import models
from django.utils.timezone import now
from .base_project_models import BaseProject


class SellingIndustrialProjectDetails(models.Model):
    project = models.ForeignKey(BaseProject, on_delete=models.CASCADE)
    total_cost = models.FloatField(default=0)

    total_materials_cost = models.FloatField(default=0)
    profit = models.FloatField(default=0)
    operating_costs = models.FloatField(default=0)

    total_cost = models.FloatField(default=0)

    # taxes
    value_added_tax = models.FloatField(default=0)
    insurance_tax = models.FloatField(default=0)
    insurance_tax_date = models.DateField()
    profits_tax = models.FloatField(default=0)


class IndustrialProjectOperationgCost(models.Model):
    project = models.ForeignKey(
        SellingIndustrialProjectDetails, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=50)
    amount = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.project.operating_costs += self.amount
        self.project.save()

    def delete(self, *args, **kwargs):
        self.project.operating_costs -= self.amount
        self.project.save()
        super().delete(*args, **kwargs)


class MaterialsSuppliers(models.Model):
    project = models.ForeignKey(
        SellingIndustrialProjectDetails, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    material_name = models.CharField(max_length=100)
    price = models.FloatField(default=0)
    quantity = models.FloatField(default=0)


class MaterialsSuppliersPayments(models.Model):
    m_supplier = models.ForeignKey(MaterialsSuppliers, on_delete=models.CASCADE)
    amount = models.FloatField(default=0)
    date = models.DateField(default=now)


class IndustrialProjectContracts(models.Model):
    project = models.ForeignKey(
        SellingIndustrialProjectDetails, on_delete=models.CASCADE
    )
    contract = models.FileField(
        upload_to="industrial_projects/contracts/", blank=True, null=True
    )
