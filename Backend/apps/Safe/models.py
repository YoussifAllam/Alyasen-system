from django.db import models
from django.utils.timezone import now


OPERATION_TYPES = [
    ("deposit", "deposit"),
    ("withdrawal", "withdrawal"),
    ("adjustment", "adjustment"),
]


class Safe(models.Model):
    balance = models.FloatField(default=0)

    class Meta:
        db_table = "safe"
        verbose_name = "Safe"
        verbose_name_plural = "Safe"


class SafeLogs(models.Model):
    trnasaction = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    amount = models.FloatField(null=True, blank=True)
    operation_type = models.CharField(
        max_length=20, choices=OPERATION_TYPES, blank=True, default=""
    )
    balance_after = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "safe_logs"
        ordering = ["-date"]
        verbose_name = "Safe Log"
        verbose_name_plural = "Safe Logs"
