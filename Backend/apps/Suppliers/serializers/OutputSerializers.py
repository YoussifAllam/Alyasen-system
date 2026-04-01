from rest_framework import serializers

from ..models import Supplier, ProjectPayment, SupplierProjectBalance

from apps.Projects.models import BaseProject


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"


class InvoicePaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPayment
        exclude = ["id", "supplier_fk", "project_fk", "portal_invoice_file"]


class SupplierInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ("name",)


class SupplierProjectsSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source="project_fk.name", read_only=True)

    class Meta:
        model = SupplierProjectBalance
        fields = ("project_fk_id", "project_name", "total", "paid", "remining")
