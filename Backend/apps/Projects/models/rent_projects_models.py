from django.db import models
from django.utils.timezone import now

from .base_project_models import BaseProject


class ProjectStatus(models.Choices):
    active = "active"
    inactive = "inactive"


class RentProjects(models.Model):
    CPB_fk = models.OneToOneField(
        "Clients.ClientProjectBalance",
        on_delete=models.CASCADE,
    )

    operating_costs = models.FloatField(default=0)
    project_status = models.CharField(
        max_length=50, choices=ProjectStatus.choices, default="active"
    )
    buying_price = models.FloatField(default=0)

    # taxes
    value_added_tax = models.FloatField(default=0)
    insurance_tax = models.FloatField(default=0)
    insurance_tax_date = models.DateField(null=True, blank=True)
    commercial_profits_tax = models.FloatField(default=0)

    # total_cost = (project.cost + operating_costs + value_added_tax)
    # net_profit = selling_price - total_cost - commercial_profits_tax

    total_cost = models.FloatField(default=0)
    net_profit = models.FloatField(default=0)
    selling_price = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        self.total_cost = (
            self.buying_price  # base_project buying cost
            + self.operating_costs  # noqa
            + self.value_added_tax  # noqa
        )
        self.net_profit = (
            self.selling_price - self.total_cost - self.commercial_profits_tax
        )
        super().save(*args, **kwargs)


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
