from rest_framework import serializers
from ..models import Client, ProjectPayment

from apps.Projects.models import BaseProject
from apps.Campaine.models import Campaine


class ClientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"


class InvoicePaymentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPayment
        exclude = ["id", "client_project_balance_fk"]


class ClientInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = (
            "name",
            "phone",
            "email",
        )


class BaseProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseProject
        fields = [
            "id",
            "name",
            "project_type",
            "client",
            "cost",
            "project_status",
            "created_date",
        ]


class CampaineSerializer(serializers.ModelSerializer):
    project_type = serializers.CharField(default="حملة", read_only=True)
    project_status = serializers.SerializerMethodField()

    class Meta:
        model = Campaine
        fields = [
            "id",
            "name",
            "project_type",
            "total_cost",
            "project_status",
            "created_date",
        ]

    def get_project_status(self, obj: Campaine):
        return obj.items.first().project.project_status
