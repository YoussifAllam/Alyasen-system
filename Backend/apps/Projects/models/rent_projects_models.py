from django.db import models
from django.utils.timezone import now
from .base_project_models import BaseProject


class ProjectStatus(models.Choices):
    active = "active"
    inactive = "inactive"


class RentProjects(models.Model):
    project = models.ForeignKey(
        BaseProject,
        on_delete=models.CASCADE,
        related_name="rent_projects",
    )
    profit = models.FloatField(default=0)
    operating_costs = models.FloatField(default=0)

    project_status = models.CharField(max_length=50, choices=ProjectStatus.choices)

    # taxes
    value_added_tax = models.FloatField(default=0)
    insurance_tax = models.FloatField(default=0)
    insurance_tax_date = models.DateField()
    profits_tax = models.FloatField(default=0)


class RentProjectContracts(models.Model):
    project = models.ForeignKey(RentProjects, on_delete=models.CASCADE)
    contract = models.FileField(
        upload_to="rent_projects/contracts/", blank=True, null=True
    )


class ProjectRentalAds(models.Model):
    project = models.ForeignKey(RentProjects, on_delete=models.CASCADE)
    ad_type = models.CharField(max_length=50)
    number = models.IntegerField(default=0)
    size = models.CharField(max_length=50)
    address = models.TextField(max_length=50)
    notes = models.TextField(max_length=50)


class RentProjectOperationgCost(models.Model):
    project = models.ForeignKey(RentProjects, on_delete=models.CASCADE)
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
