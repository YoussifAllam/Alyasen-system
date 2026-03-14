from rest_framework import serializers
from ..models import Supplier, SupplierInvoice, InvoicePayment, InvoiceMaterial


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"


class InvocesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierInvoice
        exclude = ["supplier"]
        

class InvoicePaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoicePayment
        exclude = ["id", "supplier_fk"]


class InvoiceMaterialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceMaterial
        exclude = ["invoice"]


class SupplierInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ("name",)


class InvoicesInfoSerializer(serializers.ModelSerializer):
    supplier_info = SupplierInfoSerializer(source="supplier", read_only=True)

    class Meta:
        model = SupplierInvoice
        fields = (
            "supplier_info",
            "invoice_number",
            "invoice_date",
            "invoice_total_amount",
        )
