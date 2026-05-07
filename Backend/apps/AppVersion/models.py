from django.db import models
from django.core.exceptions import ValidationError


class AppVersion(models.Model):
    version = models.CharField(max_length=20, verbose_name="رقم الإصدار")
    download_url = models.URLField(
        blank=True,
        default="",
        verbose_name="رابط التحميل",
        help_text="ضع رابط التحميل المباشر (مثال: Google Drive link). إذا تم وضعه سيتم استخدامه بدل رفع الملف.",
    )
    setup_file = models.FileField(
        upload_to="app_versions/",
        verbose_name="ملف التثبيت",
        help_text="قم برفع ملف التثبيت (setup.exe)",
    )
    notes = models.TextField(
        blank=True,
        default="",
        verbose_name="ملاحظات التحديث",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التعديل")

    class Meta:
        verbose_name = "إصدار التطبيق"
        verbose_name_plural = "إصدار التطبيق"

    def __str__(self):
        return f"إصدار التطبيق: {self.version}"

    def clean(self):
        # Only allow one instance
        if not self.pk and AppVersion.objects.exists():
            raise ValidationError(
                "يوجد إصدار بالفعل. قم بتعديل الإصدار الموجود بدلاً من إنشاء واحد جديد."
            )

        if not self.download_url and not self.setup_file:
            raise ValidationError("يجب توفير رابط تحميل أو رفع ملف التثبيت.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
