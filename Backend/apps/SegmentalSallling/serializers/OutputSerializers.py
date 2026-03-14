from rest_framework import serializers
from ..models import Invoice, SegmentalInvoiceMaterials


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = "__all__"
        # exclude = ["id"]


# class InvoicePaymentsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = InvoicePayment
#         exclude = ["id", "invoice"]


class InvoiceMaterialsSerializer(serializers.ModelSerializer):
    material_unit = serializers.ReadOnlyField(source="material.unit")
    material_name = serializers.ReadOnlyField(source="material.material_name")

    class Meta:
        model = SegmentalInvoiceMaterials
        fields = ["id", "material_name", "material_unit", "quantity_in_unit"]


# class ClientInfoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Client
#         fields = (
#             "name",
#             "phone",
#             "email",
#         )


class InvoicesInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Invoice
        fields = "__all__"
