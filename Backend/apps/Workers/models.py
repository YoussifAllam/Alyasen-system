from django.db import models

from django.utils.timezone import now
from django.core.validators import MinValueValidator


class Workers(models.Model):
    worker_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    job = models.CharField(max_length=50, default="لم يتم تعيين وظيفة له بعد")
    work_start_date = models.DateField()

    # --
    profile_picture = models.ImageField(default="default.webp", upload_to="workers/")

    # --
    total_days_of_absence = models.IntegerField(default=0)
    total_days_of_work = models.IntegerField(default=0)
    is_in_vacation = models.BooleanField(default=False)

    # --
    daily_salary = models.FloatField(default=0)
    total_advance = models.IntegerField(default=0)
    total_deduction = models.IntegerField(default=0)
    total_alternatives_amount = models.FloatField(default=0)
    remaining_salary = models.FloatField(default=0)

    work_start_date = models.DateField(editable=True)

    class Meta:
        db_table = "workers"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["phone"]),
        ]
        verbose_name = "Worker"
        verbose_name_plural = "Workers"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # For new instances
        if not self.pk and not self.work_start_date:
            self.work_start_date = now().date()
        super().save(*args, **kwargs)


class WorkerAlternatives(models.Model):
    worker = models.ForeignKey(Workers, on_delete=models.CASCADE)
    reason = models.TextField(null=True, blank=True)
    date = models.DateField()
    amount = models.FloatField(MinValueValidator(0))

    class Meta:
        db_table = "worker_alternatives"
        verbose_name = "Worker Alternative"
        verbose_name_plural = "Worker Alternatives"
        indexes = [
            models.Index(fields=["worker"]),
        ]


class WorkerAbsence(models.Model):
    worker = models.ForeignKey(Workers, on_delete=models.CASCADE)
    absence_date = models.DateField()
    absence_reason = models.TextField(null=True, blank=True)


class WorkerDeduction(models.Model):
    worker = models.ForeignKey(Workers, on_delete=models.CASCADE)
    deduction_date = models.DateField()
    deduction_amount = models.FloatField(MinValueValidator(0))
    deduction_reason = models.TextField(null=True, blank=True)


class WorkerAdvance(models.Model):
    worker = models.ForeignKey(Workers, on_delete=models.CASCADE)
    advance_date = models.DateField()
    advance_amount = models.FloatField(MinValueValidator(0))
    advance_reason = models.TextField(null=True, blank=True)


class WorkersPaidSalary(models.Model):
    worker = models.ForeignKey(Workers, on_delete=models.CASCADE)
    advance = models.ForeignKey(WorkerAdvance, on_delete=models.SET_NULL, null=True, blank=True)
    paid_date = models.DateField()
    paid_amount = models.FloatField(MinValueValidator(0))


class Attendance(models.Model):
    worker = models.ForeignKey(Workers, on_delete=models.CASCADE)
    enter_date = models.DateTimeField(null=True)
    exit_date = models.DateTimeField(null=True)
    attendance_date = models.DateField(auto_now_add=True)  # Add this field

    class Meta:
        verbose_name = "Attendance"
        verbose_name_plural = "Attendances"
        indexes = [
            models.Index(fields=["worker"]),
            models.Index(fields=["attendance_date"]),
        ]
