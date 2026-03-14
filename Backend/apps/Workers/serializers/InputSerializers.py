from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from .. import models
from ..db_queries import selectors
from ..tasks import worker_tasks


class WorkersSerializer(ModelSerializer):
    profile_picture = serializers.ImageField(
        required=False, max_length=None, allow_empty_file=False, use_url=True
    )

    class Meta:
        model = models.Workers
        fields = ["name", "phone", "profile_picture"]

    def validate_profile_picture(self, value):
        if not value:
            return value

        # File size validation (5MB)
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Image file too large. Maximum size is 5MB.")

        # File extension validation
        valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        import os

        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_extensions:
            raise serializers.ValidationError(
                f"Unsupported file extension. Allowed: {', '.join(valid_extensions)}"
            )

        # Content type validation
        valid_content_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
        ]
        if hasattr(value, "content_type") and value.content_type not in valid_content_types:
            raise serializers.ValidationError("Invalid image format.")

        return value


class WorkerInfoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Workers
        fields = ["name", "phone", "job", "profile_picture", "daily_salary", "work_start_date"]
        extra_kwargs = {
            # "work_start_date": {"required": False},
            "name": {"required": False},
            "phone": {"required": False},
            "job": {"required": False},
            "profile_picture": {"required": False},
            "daily_salary": {"required": False},
        }


class WorkerAbsenceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkerAbsence
        fields = "__all__"
        extra_kwargs = {"worker": {"required": False}}

    def validate_absence_date(self, absence_date):
        # absence_date = attrs["absence_date"]
        if selectors.check_if_absence_date_is_exist(absence_date):
            raise serializers.ValidationError("يوم الغياب هذا موجود بالفعل")

        worker_instance = self.context.get("worker_instance")
        if not worker_tasks.check_if_absence_date_is_valid(absence_date, worker_instance):
            raise serializers.ValidationError("يوم الغياب غير صحيح")
        return absence_date


class WorkerDeductionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkerDeduction
        fields = "__all__"
        extra_kwargs = {"worker": {"required": False}}

    def validate_deduction_date(self, deduction_date):
        worker_instance = self.context.get("worker_instance")
        if not worker_tasks.check_if_absence_date_is_valid(deduction_date, worker_instance):
            raise serializers.ValidationError("يوم الخصم غير صحيح")
        return deduction_date


class WorkerAdvanceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkerAdvance
        fields = "__all__"
        extra_kwargs = {"worker": {"required": False}}

    def validate_advance_date(self, advance_date):
        worker_instance = self.context.get("worker_instance")
        if not worker_tasks.check_if_absence_date_is_valid(advance_date, worker_instance):
            raise serializers.ValidationError("يوم السلفه غير صحيح")
        return advance_date


class WorkerAlternativesCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WorkerAlternatives
        fields = "__all__"
        extra_kwargs = {"worker": {"required": False}}

    def validate_date(self, advance_date):
        worker_instance = self.context.get("worker")
        if not worker_tasks.check_if_absence_date_is_valid(advance_date, worker_instance):
            raise serializers.ValidationError("التاريخ غير صحيح")
        return advance_date
