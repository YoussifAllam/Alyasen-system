from rest_framework import serializers
from ..models import Supplier, InvoicePayment


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"


class InvoicePaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoicePayment
        exclude = ["id", "supplier_fk"]


class SupplierInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ("name",)
