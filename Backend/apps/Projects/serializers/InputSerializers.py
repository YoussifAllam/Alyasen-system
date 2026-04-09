from rest_framework import serializers
from .. import models


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BaseProject
        fields = ["name", "project_type", "project_status", "supplier", "cost"]


class RentProjectsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RentProjects
        fields = [
            "selling_price",
            "value_added_tax",
            "commercial_profits_tax",
            "insurance_tax",
            "insurance_tax_date",
        ]
