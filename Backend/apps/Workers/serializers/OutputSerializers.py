from rest_framework import serializers
from ..models import Workers, WorkerAbsence, WorkerDeduction, WorkerAdvance, Attendance, WorkerAlternatives

from django.utils.timezone import now


class WorkersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workers
        fields = (
            "worker_id",
            "name",
            "phone",
        )


class WorkersInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workers
        fields = "__all__"


class WorkerAbsenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerAbsence
        exclude = ["worker"]


class WorkerDeductionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerDeduction
        exclude = ["worker"]


class WorkerAdvanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerAdvance
        exclude = ["worker"]


class WorkerAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        exclude = ["worker", "id", "attendance_date"]


class WorkerAlternativesSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerAlternatives
        exclude = ["worker"]


class SalaryReportSerializer(serializers.ModelSerializer):
    date = serializers.CharField(default=now().strftime("%Y-%m-%d"))

    class Meta:
        model = Workers
        fields = (
            "name",
            "date",
            "total_days_of_work",
            "daily_salary",
            "total_alternatives_amount",
            "phone",
            "total_advance",
            "total_days_of_absence",
            "total_deduction",
            "remaining_salary",
        )
