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
    paid = serializers.SerializerMethodField()
    remining = serializers.SerializerMethodField()

    class Meta:
        model = BaseProject
        fields = [
            "id",
            "name",
            "project_type",
            "cost",
            "paid",
            "remining",
            "project_status",
            "created_date",
        ]

    def get_paid(self, obj: BaseProject):
        balance = obj.clientprojectbalance_set.first()
        return balance.paid if balance else 0

    def get_remining(self, obj: BaseProject):
        balance = obj.clientprojectbalance_set.first()
        return balance.remining if balance else 0


class CampaineSerializer(serializers.ModelSerializer):
    project_type = serializers.CharField(default="حملة", read_only=True)
    project_status = serializers.SerializerMethodField()
    paid = serializers.SerializerMethodField()
    remining = serializers.SerializerMethodField()

    class Meta:
        model = Campaine
        fields = [
            "id",
            "name",
            "project_type",
            "total_cost",
            "paid",
            "remining",
            "project_status",
            "created_date",
        ]

    def get_project_status(self, obj: Campaine):
        return obj.items.first().project.project_status

    def get_paid(self, obj: Campaine):
        balance = obj.clientprojectbalance_set.first()
        return balance.paid if balance else 0

    def get_remining(self, obj: Campaine):
        balance = obj.clientprojectbalance_set.first()
        return balance.remining if balance else 0
