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
    project_status = models.CharField(max_length=50, choices=ProjectStatus.choices)
    created_date = models.DateField(default=now)

    class Meta:
        db_table = "Projects"
        indexes = [
            models.Index(fields=["created_date"]),
            models.Index(fields=["project_type"]),
        ]
        ordering = ["-created_date"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"


class ProjectContracts(models.Model):
    project = models.ForeignKey(BaseProject, on_delete=models.CASCADE)
    contract = models.FileField(upload_to="contracts/", blank=True, null=True)
