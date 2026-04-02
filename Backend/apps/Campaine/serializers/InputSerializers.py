from rest_framework import serializers
from django.db import transaction
from ..models import Campaine, CampaineItem
from apps.Projects.models import BaseProject
from apps.Suppliers.models import Supplier
from apps.Clients.models import Client


class CampaineItemSerializer(serializers.ModelSerializer):
    # Make project required and validate it exists
    project_id = serializers.PrimaryKeyRelatedField(
        source="project", queryset=BaseProject.objects.all(), write_only=True
    )
    supplier_id = serializers.PrimaryKeyRelatedField(
        source="supplier", queryset=Supplier.objects.all(), write_only=True
    )

    # Read-only fields to show project details in response
    project_name = serializers.CharField(source="project.name", read_only=True)
    project_cost = serializers.FloatField(source="project.cost", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = CampaineItem
        fields = [
            "id",
            "project_id",
            "supplier_id",
            "project_name",
            "project_cost",
            "supplier_name",
        ]

    def validate(self, data):
        # Validate that project and supplier are provided
        if not data.get("project"):
            raise serializers.ValidationError({"project_id": "Project is required"})
        if not data.get("supplier"):
            raise serializers.ValidationError({"supplier_id": "Supplier is required"})
        return data


class CampaineSerializer(serializers.ModelSerializer):
    items = CampaineItemSerializer(many=True, write_only=True)
    total_cost = serializers.FloatField(read_only=True)

    class Meta:
        model = Campaine
        fields = ["id", "name", "client", "total_cost", "created_date", "items"]
        read_only_fields = ["created_date"]

    def validate_items(self, value):
        """Validate that at least one item is provided"""
        if not value:
            raise serializers.ValidationError("At least one campaign item is required")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items")

        # Calculate total cost from all projects
        total_cost = 0
        for item_data in items_data:
            project = item_data.get("project")
            if project and project.cost:
                total_cost += project.cost

        # Create campaign with calculated total cost
        campaign = Campaine.objects.create(total_cost=total_cost, **validated_data)

        # Create all campaign items
        campaign_items = []
        for item_data in items_data:
            campaign_item = CampaineItem(campaine=campaign, **item_data)
            campaign_items.append(campaign_item)

        # Bulk create for better performance
        CampaineItem.objects.bulk_create(campaign_items)

        return campaign
