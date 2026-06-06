from django.db import models


class CompanyAssets(models.Model):
    CATEGORY_EQUIPMENT = "equipment"
    CATEGORY_VEHICLE = "vehicle"
    CATEGORY_FURNITURE = "furniture"
    CATEGORY_ELECTRONICS = "electronics"
    CATEGORY_OTHER = "other"

    CATEGORY_CHOICES = [
        (CATEGORY_EQUIPMENT, "معدات"),
        (CATEGORY_VEHICLE, "مركبة"),
        (CATEGORY_FURNITURE, "أثاث"),
        (CATEGORY_ELECTRONICS, "إلكترونيات"),
        (CATEGORY_OTHER, "أخرى"),
    ]

    STATUS_WORKING = "working"
    STATUS_MAINTENANCE = "maintenance"
    STATUS_RETIRED = "retired"

    STATUS_CHOICES = [
        (STATUS_WORKING, "يعمل"),
        (STATUS_MAINTENANCE, "تحت الصيانة"),
        (STATUS_RETIRED, "متقاعد"),
    ]

    name = models.CharField(max_length=100)
    price = models.FloatField(default=0)
    category = models.CharField(
        max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_OTHER
    )
    purchase_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_WORKING
    )
    useful_life_years = models.PositiveSmallIntegerField(null=True, blank=True)
    depreciation_value = models.FloatField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True, default="")
    responsible_person = models.CharField(max_length=100, blank=True, default="")
    details = models.TextField(blank=True, default="")

    def __str__(self):
        return self.name

    class Meta:
        db_table = "company_assets"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["category"]),
            models.Index(fields=["status"]),
            models.Index(fields=["purchase_date"]),
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
