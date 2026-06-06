from rest_framework.serializers import ModelSerializer

from .. import models


class MachineSerializer(ModelSerializer):
    class Meta:
        model = models.CompanyAssets
        fields = (
            "name",
            "price",
            "category",
            "purchase_date",
            "status",
            "useful_life_years",
            "depreciation_value",
            "location",
            "responsible_person",
            "details",
        )
