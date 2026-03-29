from rest_framework import serializers
from .. import models
from apps.Suppliers.serializers.OutputSerializers import SupplierSerializer


class ProjectContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProjectContracts
        fields = ["id", "contract"]


class BaseProjectsNamesSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.BaseProject
        fields = [
            "id",
            "name",
            "project_type",
            "project_status",
            "created_date",
        ]
