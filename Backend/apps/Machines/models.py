from django.db import models
from django.utils.timezone import now


class Machines(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(default="default.webp", upload_to="machines/")
    last_repair_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "machines"
        indexes = [
            models.Index(fields=["name"]),
        ]
        verbose_name = "Machines"
        verbose_name_plural = "Machine"


class MachineComponents(models.Model):
    name = models.CharField(max_length=100)
    machine = models.ForeignKey(Machines, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=["machine"]),
        ]

    def __str__(self):
        return self.name


class MachineRepairHistory(models.Model):
    details = models.TextField()
    amount = models.FloatField()
    date = models.DateField(default=now)
    machine = models.ForeignKey(Machines, on_delete=models.CASCADE)

    class Meta:
        db_table = "machine_repair_history"
        verbose_name = "Machine Repair History"
        verbose_name_plural = "Machine Repair History"
        indexes = [
            models.Index(fields=["machine"]),
        ]
