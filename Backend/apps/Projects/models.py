from django.db import models
from django.utils.timezone import now


class ProjectTypes(models.Choices):
    rent = "rent"
    industrial = "industrial"


class ProjectStatus(models.Choices):
    active = "active"
    inactive = "inactive"


class PaymentStatus(models.Choices):
    pendding = "pendding"
    paid = "paid"


class Projects(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    project_type = models.CharField(max_length=50, choices=ProjectTypes.choices)
    project_status = models.CharField(max_length=50, choices=ProjectStatus.choices)
    created_date = models.DateField(default=now)

    operating_costs = models.FloatField(default=0)

    # taxes
    value_added_tax = models.FloatField(default=0)
    insurance_tax = models.FloatField(default=0)
    profits_tax = models.FloatField(default=0)

    project_total_cost = models.FloatField(default=0)

    class Meta:
        db_table = "Projects"
        indexes = [
            models.Index(fields=["created_date"]),
            models.Index(fields=["project_type"]),
        ]
        ordering = ["-created_date"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.username


class ProjectContracts(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    contract = models.FileField(upload_to="contracts/", blank=True, null=True)


class ProjectRentalAds(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    ad_type = models.CharField(max_length=50)
    number = models.IntegerField(default=0)
    size = models.CharField(max_length=50)
    address = models.TextField(max_length=50)
    notes = models.TextField(max_length=50)


class ProjectOperationgCost(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
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


class GuaranteeCheques(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    cheque_number = models.CharField(max_length=50)
    cheque_date = models.DateField()
    cheque_amount = models.FloatField(default=0)


class ProjectInsuranceTax(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    insurance_tax = models.FloatField(default=0)
    insurance_tax_date = models.DateField()


class ProjectPayments(models.Model):
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    payment_date = models.DateField()
    payment_amount = models.FloatField(default=0)
    payment_method = models.CharField(max_length=50)
    payment_status = models.CharField(max_length=50, default=PaymentStatus.pendding)
    payment_notes = models.TextField(max_length=50)
    # i will use it just if the payment_method is cheque
    checqu_clear_date = models.DateField(null=True, blank=True)
