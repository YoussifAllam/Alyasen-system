from rest_framework import serializers
from ..models import Client

from apps.Projects.models import BaseProject
from apps.Campaine.models import Campaine


class ClientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"


# class ClientPaymentsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = InvoicePayment
#         exclude = ["id", "client_fk"]


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
