from rest_framework.serializers import ModelSerializer, ImageField, ValidationError
from .. import models


class MachineSerializer(ModelSerializer):
    image = ImageField(required=False, max_length=None, allow_empty_file=False, use_url=True)

    class Meta:
        model = models.Machines
        fields = (
            "name",
            "image",
        )

    def validate_profile_picture(self, value):
        if not value:
            return value

        # File size validation (5MB)
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise ValidationError("Image file too large. Maximum size is 5MB.")

        # File extension validation
        valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
        import os

        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_extensions:
            raise ValidationError(f"Unsupported file extension. Allowed: {', '.join(valid_extensions)}")

        # Content type validation
        valid_content_types = [
            "image/jpeg",
            "image/png",
            "image/webp",
        ]
        if hasattr(value, "content_type") and value.content_type not in valid_content_types:
            raise ValidationError("Invalid image format.")

        return value


class MachineComponentsSerializer(ModelSerializer):
    class Meta:
        model = models.MachineComponents
        fields = "__all__"


class MachineRepairHistorySerializer(ModelSerializer):
    class Meta:
        model = models.MachineRepairHistory
        fields = "__all__"
        extra_kwargs = {"machine": {"required": False}}
