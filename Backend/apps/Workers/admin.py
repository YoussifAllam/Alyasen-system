from django.contrib import admin
from . import models
from unfold.admin import ModelAdmin


@admin.register(models.Workers)
class WorkersClass(ModelAdmin):
    list_display = ("name", "work_start_date")


@admin.register(models.WorkersPaidSalary)
class WorkersPaidSalaryClass(ModelAdmin):
    list_display = ("paid_amount",)


@admin.register(models.Attendance)
class AttendanceClass(ModelAdmin):
    list_display = ("worker",)
