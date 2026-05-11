from rest_framework import serializers
from ..models import Client, ProjectPayment, ClientProjectBalance

from apps.Projects.models import BaseProject
from apps.Campaine.models import Campaine


class ClientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"


class InvoicePaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPayment
        exclude = ["client_project_balance_fk"]


class ClientInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = (
            "name",
            "phone",
            "email",
        )


class BaseProjectSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = BaseProject
        fields = ["id", "name", "supplier_name", "project_type"]


class CampaineSerializer(serializers.ModelSerializer):
    suppliers = serializers.SerializerMethodField()

    class Meta:
        model = Campaine
        fields = ["id", "name", "suppliers"]

    def get_suppliers(self, obj: Campaine):
        # Already prefetch if possible in view
        if hasattr(obj, "_prefetched_items"):
            return [item.supplier.name for item in obj.items.all()]
        return list(
            obj.items.select_related("supplier")
            .values_list("supplier__name", flat=True)
            .distinct()
        )


class CBPSerializer(serializers.ModelSerializer):
    project_type = serializers.SerializerMethodField()
    project_name = serializers.SerializerMethodField()
    project_status = serializers.SerializerMethodField()

    class Meta:
        model = ClientProjectBalance
        fields = [
            "id",
            "project_name",
            "project_type",
            "total",
            "paid",
            "remining",
            "project_status",
            "created_date",
        ]

    def get_project_type(self, obj: ClientProjectBalance):
        if obj.project_fk:
            return obj.project_fk.project_type
        return "حملة"

    def get_project_name(self, obj: ClientProjectBalance):
        if obj.project_fk:
            return obj.project_fk.name
        return obj.campaine_fk.name

    def get_project_status(self, obj: ClientProjectBalance):
        if obj.project_fk:
            return obj.project_fk.project_status
        return obj.campaine_fk.items.first().project.project_status
