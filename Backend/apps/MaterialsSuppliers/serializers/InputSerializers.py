from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .. import models


class SupplierSerializer(ModelSerializer):
    profile_picture = serializers.ImageField(
        required=False, max_length=None, allow_empty_file=False, use_url=True
    )

    class Meta:
        model = models.MaterialSupplier
        fields = [
            "name",
            "phone",
            "email",
            "profile_picture",
            "total_amount_due",
            "total_amount_payable",
        ]
        read_only_fields = ["total_paid_amount"]
        extra_kwargs = {"email": {"required": False}}

    def validate_profile_picture(self, value):
        if not value:
            return value

        # File size validation (5MB)
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                "Image file too large. Maximum size is 5MB."
            )

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
        if (
            hasattr(value, "content_type")
            and value.content_type not in valid_content_types
        ):
            raise serializers.ValidationError("Invalid image format.")

        return value


class InvoicesSerializer(ModelSerializer):
    class Meta:
        model = models.SupplierInvoice
        fields = "__all__"
        extra_kwargs = {"supplier": {"required": False}}


class InvoiceInfoUpdateSerializer(ModelSerializer):
    class Meta:
        model = models.SupplierInvoice
        fields = (
            "first_weight",
            "second_weight",
            "driver_name",
            "driver_phone",
            "car_plate_number",
            "karta_number",
        )


class InvoiceMaterials(ModelSerializer):
    class Meta:
        model = models.InvoiceMaterial
        fields = [
            "id",
            "invoice",
            "material_name",
            "quantity_in_unit",
            "buy_price_per_unit",
            "unit",
        ]
        extra_kwargs = {"invoice": {"required": False}}
