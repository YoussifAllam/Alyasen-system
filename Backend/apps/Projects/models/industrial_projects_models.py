from django.db import models
from django.utils.timezone import now


class ProjectStatus(models.Choices):
    active = "active"
    inactive = "inactive"


class SellingIndustrialProjectDetails(models.Model):
    CPB_fk = models.OneToOneField(
        "Clients.ClientProjectBalance",
        on_delete=models.CASCADE,
    )

    operating_costs = models.FloatField(default=0)
    project_status = models.CharField(
        max_length=50, choices=ProjectStatus.choices, default="active"
    )
    buying_price = models.FloatField(default=0)
    total_materials_cost = models.FloatField(default=0)

    # taxes
    value_added_tax = models.FloatField(default=0)
    insurance_tax = models.FloatField(default=0)
    insurance_tax_date = models.DateField(null=True, blank=True)
    insurance_tax_cleared = models.BooleanField(default=False)
    commercial_profits_tax = models.FloatField(default=0)

    # total_cost = (project.cost + operating_costs + total_materials_cost + value_added_tax)
    # net_profit = selling_price - total_cost - commercial_profits_tax

    total_cost = models.FloatField(default=0)
    net_profit = models.FloatField(default=0)
    selling_price = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        self.total_cost = (
            self.buying_price  # base_project buying cost
            + self.operating_costs  # noqa
            + self.total_materials_cost  # noqa
            + self.value_added_tax  # noqa
        )
        self.net_profit = (
            self.selling_price - self.total_cost - self.commercial_profits_tax
        )
        super().save(*args, **kwargs)


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


class IndustrialProjectContracts(models.Model):
    project = models.ForeignKey(
        SellingIndustrialProjectDetails, on_delete=models.CASCADE
    )
    contract = models.FileField(
        upload_to="industrial_projects/contracts/", blank=True, null=True
    )


class SellingIndustrialProjectGuaranteeCheques(models.Model):
    project = models.OneToOneField(
        SellingIndustrialProjectDetails, on_delete=models.CASCADE
    )
    cheque_number = models.CharField(max_length=50)
    cheque_date = models.DateField()
    cheque_amount = models.FloatField(default=0)


# class MaterialsSuppliers(models.Model):
#     project = models.ForeignKey(
#         SellingIndustrialProjectDetails, on_delete=models.CASCADE
#     )
#     name = models.CharField(max_length=100)
#     phone = models.CharField(max_length=100)
#     material_name = models.CharField(max_length=100)
#     price = models.FloatField(default=0)
#     quantity = models.FloatField(default=0)


# class MaterialsSuppliersPayments(models.Model):
#     m_supplier = models.ForeignKey(MaterialsSuppliers, on_delete=models.CASCADE)
#     amount = models.FloatField(default=0)
#     date = models.DateField(default=now)
