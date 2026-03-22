from django.db import models
from django.utils.timezone import now


class CompanyAssets(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(default="default.webp", upload_to="CompanyAssets/")

    def __str__(self):
        return self.name

    class Meta:
        db_table = "company_assets"
        indexes = [
            models.Index(fields=["name"]),
        ]
        verbose_name = "CompanyAssets"
        verbose_name_plural = "CompanyAssets"
