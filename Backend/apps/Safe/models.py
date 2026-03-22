from django.db import models
from django.utils.timezone import now


class Safe(models.Model):
    balance = models.DecimalField(max_digits=20, decimal_places=3, default=0)

    class Meta:
        db_table = "safe"
        verbose_name = "Safe"
        verbose_name_plural = "Safe"


class SafeLogs(models.Model):
    trnasaction = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "safe_logs"
        ordering = ["date"]
        verbose_name = "Safe Log"
        verbose_name_plural = "Safe Logs"
