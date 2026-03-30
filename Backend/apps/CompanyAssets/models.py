from django.db import models
from django.utils.timezone import now


class CompanyAssets(models.Model):
    name = models.CharField(max_length=100)
    price = models.FloatField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "company_assets"
        indexes = [
            models.Index(fields=["name"]),
        ]
        verbose_name = "CompanyAssets"
        verbose_name_plural = "CompanyAssets"


class CompanyAssetsAttachments(models.Model):
    asset = models.ForeignKey(
        CompanyAssets, on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(upload_to="CompanyAssetsAttachments/")

    def __str__(self):
        return f"{self.asset.name} - {self.file.name}"

    class Meta:
        db_table = "company_assets_attachments"
        verbose_name = "CompanyAssetsAttachments"
        verbose_name_plural = "CompanyAssetsAttachments"
