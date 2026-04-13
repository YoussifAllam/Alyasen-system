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
    project_name = serializers.SerializerMethodField()

    class Meta:
        model = models.RentProjects
        fields = [
            "id",
            "project_name",
            "operating_costs",
            "buying_price",
            "total_cost",
            "selling_price",
            "net_profit",
            "value_added_tax",
            "insurance_tax",
            "insurance_tax_date",
            "insurance_tax_cleared",
            "commercial_profits_tax",
            "contracts",
        ]

    def get_project_name(self, obj: models.RentProjects):
        return obj.CPB_fk.project_name


class RentProjectAdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProjectRentalAds
        fields = "__all__"


class RentProjectGuaranteeChequesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RentProjectsGuaranteeCheques
        fields = "__all__"


class RentProjectOperationgCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RentProjectOperationgCost
        fields = "__all__"


# ____


class SellingIndustrialProjectContractsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndustrialProjectContracts
        fields = ["id", "contract"]


class SellingIndustrialProjectDetailsSerializer(serializers.ModelSerializer):
    contracts = SellingIndustrialProjectContractsSerializer(
        many=True, source="industrialprojectcontracts_set"
    )
    project_name = serializers.SerializerMethodField()

    class Meta:
        model = models.SellingIndustrialProjectDetails
        fields = [
            "id",
            "project_name",
            "operating_costs",
            "buying_price",
            "total_cost",
            "selling_price",
            "net_profit",
            "total_materials_cost",
            "value_added_tax",
            "insurance_tax",
            "insurance_tax_date",
            "insurance_tax_cleared",
            "commercial_profits_tax",
            "contracts",
        ]

    def get_project_name(self, obj: models.SellingIndustrialProjectDetails):
        return obj.CPB_fk.project_name


class SellingIndustrialProjectGuaranteeChequesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SellingIndustrialProjectGuaranteeCheques
        fields = "__all__"


class SellingIndustrialProjectOperationgCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndustrialProjectOperationgCost
        fields = "__all__"
