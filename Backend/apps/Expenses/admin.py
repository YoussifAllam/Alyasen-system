from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


# @admin.register(models.Expenses)
# class TransactionsLogClass(ModelAdmin):
#     list_display = ("transaction", "created_date")
#     list_filter = ("transaction",)
#     ordering = ["-created_date"]
