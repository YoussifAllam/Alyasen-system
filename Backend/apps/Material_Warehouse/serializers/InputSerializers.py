from rest_framework.serializers import ModelSerializer
from .. import models


class MaterialSerializer(ModelSerializer):
    class Meta:
        model = models.MaterialWarehouse
        fields = "__all__"


class UpdateMaterialSerializer(ModelSerializer):
    class Meta:
        model = models.MaterialWarehouse
        fields = ["material_name", "buy_price_per_unit"]
        extra_kwargs = {"material_name": {"required": False}, "buy_price_per_unit": {"required": False}}
