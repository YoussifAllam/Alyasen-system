from django.db import models
from django.utils.timezone import now


class ProjectTypes(models.Choices):
    rent = "rent"
    industrial = "industrial"
    selling = "selling"


class ProjectStatus(models.Choices):
    active = "active"
    inactive = "inactive"


class BaseProject(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    project_type = models.CharField(max_length=50, choices=ProjectTypes.choices)
    client = models.ForeignKey(
        "Clients.Client", on_delete=models.SET_NULL, null=True, blank=True
    )
    project_status = models.CharField(
        max_length=50, choices=ProjectStatus.choices, default="active"
    )
    cost = models.FloatField()
    supplier = models.ForeignKey(
        "Suppliers.Supplier", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_date = models.DateField(default=now)

    class Meta:
        indexes = [
            models.Index(fields=["created_date"]),
            models.Index(fields=["project_type"]),
        ]
        ordering = ["-created_date"]
        verbose_name = "BaseProject"
        verbose_name_plural = "BaseProjects"

    def __str__(self):
        return f"{self.id}"


class ProjectContracts(models.Model):
    project = models.ForeignKey(BaseProject, on_delete=models.CASCADE)
    contract = models.FileField(upload_to="contracts/", blank=True, null=True)


class ProjectsGuaranteeCheques(models.Model):
    project = models.ForeignKey(BaseProject, on_delete=models.CASCADE)
    cheque_number = models.CharField(max_length=50)
    cheque_date = models.DateField()
    cheque_amount = models.FloatField(default=0)
