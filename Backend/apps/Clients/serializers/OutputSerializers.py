from rest_framework import serializers
from ..models import Client, ClientInvoice, InvoicePayment, InvoiceMaterials


class ClientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"


class InvocesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientInvoice
        exclude = ["client",]


class ClientPaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoicePayment
        exclude = ["id", "client_fk"]


class InvoiceMaterialsSerializer(serializers.ModelSerializer):
    material_name = serializers.ReadOnlyField(source="material.material_name")
    material_id = serializers.ReadOnlyField(source="material.id")
    material_unit = serializers.ReadOnlyField(source="material.unit")

    class Meta:
        model = InvoiceMaterials
        fields = ["id", "material_name", "material_id", "quantity_in_unit", "material_unit"]


class ClientInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = (
            "name",
            "phone",
            "email",
        )


class InvoicesInfoSerializer(serializers.ModelSerializer):
    client_info = ClientInfoSerializer(source="client", read_only=True)

    class Meta:
        model = ClientInvoice
        fields = (
            "client_info",
            "invoice_number",
            "invoice_date",
            "invoice_total_amount",
            "total_amount_payable",
            "total_paid_amount",
        )
