from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .. import models


class ClientsSerializer(ModelSerializer):
    profile_picture = serializers.ImageField(
        required=False, max_length=None, allow_empty_file=False, use_url=True
    )

    class Meta:
        model = models.Client
        fields = [
            "name",
            "phone",
            "email",
            "profile_picture",
            "total_balance_owed_to_us",
            "total_remaining_balance_owed_to_us",
        ]
        read_only_fields = (
            "total_paid_amount",
        )
        extra_kwargs = {"email": {"required": False}}

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


class ClientUpdateSerializer(ModelSerializer):

    class Meta:
        model = models.Client
        fields = [
            "name",
            "phone",
            "email",
            
        ]
        
        extra_kwargs = {"email": {"required": False},"phone": {"required": False},"name": {"required": False}}


class InvoicesSerializer(ModelSerializer):
    class Meta:
        model = models.ClientInvoice
        fields = "__all__"
        extra_kwargs = {"client": {"required": False}}


class InvoiceMaterialsSerializer(ModelSerializer):
    class Meta:
        model = models.InvoiceMaterials
        fields = [
            "invoice",
            "material",
            "quantity_in_unit",
        ]
        extra_kwargs = {"invoice": {"required": False}, "material": {"required": False}}
