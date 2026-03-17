from django.db import models
from django.utils.timezone import now


# class TransactionsLog(models.Model):
#     username = models.CharField(max_length=50, blank=True, null=True)
#     transaction = models.TextField()
#     created_date = models.DateField(default=now)

#     class Meta:
#         db_table = "TransactionsLog"
#         indexes = [
#             models.Index(fields=["created_date"]),
#             models.Index(fields=["username"]),
#             models.Index(fields=["username", "created_date"]),
#         ]
#         ordering = ["-created_date"]
#         verbose_name = "Transaction Log"
#         verbose_name_plural = "Transaction Logs"

#     def __str__(self):
#         return self.username
