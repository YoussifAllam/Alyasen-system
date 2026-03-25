from django.db import models
from django.utils.timezone import now


class ProjectStatus(models.Choices):
    active = "active"
    inactive = "inactive"


class PaymentStatus(models.Choices):
    pendding = "pendding"
    paid = "paid"


class RentProjects(models.Model):
    project = models.ForeignKey(
        "base_project_models.BaseProject",
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


class RentGuaranteeCheques(models.Model):
    project = models.ForeignKey(RentProjects, on_delete=models.CASCADE)
    cheque_number = models.CharField(max_length=50)
    cheque_date = models.DateField()
    cheque_amount = models.FloatField(default=0)


class RentProjectPayments(models.Model):
    project = models.ForeignKey(RentProjects, on_delete=models.CASCADE)
    payment_date = models.DateField()
    payment_amount = models.FloatField(default=0)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=50, default=PaymentStatus.pendding)
    payment_notes = models.TextField(max_length=50)
    #  use it just if the payment_method is cheque
    checqu_clear_date = models.DateField(null=True, blank=True)
