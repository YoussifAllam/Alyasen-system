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


class RentProjectAdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProjectRentalAds
        fields = "__all__"
        extra_kwargs = {"project": {"required": False}}


class RentProjectGuaranteeChequesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RentProjectsGuaranteeCheques
        fields = "__all__"
        extra_kwargs = {"project": {"required": False}}


class RentProjectOperationgCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RentProjectOperationgCost
        fields = "__all__"
        extra_kwargs = {"project": {"required": False}}


# ___


class SellingIndustrialProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SellingIndustrialProjectDetails
        fields = [
            "selling_price",
            "value_added_tax",
            "commercial_profits_tax",
            "insurance_tax",
            "insurance_tax_date",
        ]


class SellingIndustrialProjectGuaranteeChequesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SellingIndustrialProjectGuaranteeCheques
        fields = "__all__"
        extra_kwargs = {"project": {"required": False}}


class SellingIndustrialProjectOperationgCostSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndustrialProjectOperationgCost
        fields = "__all__"
        extra_kwargs = {"project": {"required": False}}
