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


class RentProjectsContractsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RentProjectContracts
        fields = ["id", "contract"]


class RentProjectInfoSerializer(serializers.ModelSerializer):
    contracts = RentProjectsContractsSerializer(
        many=True, source="rentprojectcontracts_set"
    )

    class Meta:
        model = models.RentProjects
        fields = [
            "id",
            "operating_costs",
            "buying_price",
            "total_cost",
            "selling_price",
            "net_profit",
            "value_added_tax",
            "insurance_tax",
            "insurance_tax_date",
            "commercial_profits_tax",
            "contracts",
        ]
