from rest_framework import serializers
from apps.Campaine.models import Campaine, CampaineItem
from apps.Clients.models import Client
from apps.Suppliers.models import Supplier
from apps.Projects.models import BaseProject

class CampaineItemSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = CampaineItem
        fields = ["id", "supplier", "supplier_name", "project", "project_name", "amount"]

class CampaineSerializer(serializers.ModelSerializer):
    items = CampaineItemSerializer(many=True, required=False)
    client_name = serializers.CharField(source="client.name", read_only=True)

    class Meta:
        model = Campaine
        fields = ["id", "name", "client", "client_name", "total_cost", "created_date", "items"]
