from rest_framework import serializers
from ..models import Mixtures, MixtureMaterial

from apps.Material_Warehouse.models import MaterialWarehouse


class MixturesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mixtures
        fields = "__all__"


class MaterialWarehouseSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()
    proft = serializers.SerializerMethodField()

    class Meta:
        model = MaterialWarehouse
        fields = (
            "material_name",
            "buy_price_per_kilo",
            "price_per_kilo",
            "total_price",
            "proft",
        )


class MixtureMaterialsSerializer(serializers.ModelSerializer):
    material_name = serializers.SerializerMethodField()
    material_buy_price_per_kilo = serializers.SerializerMethodField()
    material_sell_price_per_kilo = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    total_profit = serializers.SerializerMethodField()

    class Meta:
        model = MixtureMaterial
        fields = [
            "id",
            "quantity_used",
            "material_name",
            "material_buy_price_per_kilo",
            "material_sell_price_per_kilo",
            "total_price",
            "total_profit",
        ]

    def get_material_name(self, obj: MixtureMaterial):
        return obj.material_fk.material_name

    def get_material_buy_price_per_kilo(self, obj: MixtureMaterial):
        return obj.material_fk.buy_price_per_kilo

    def get_material_sell_price_per_kilo(self, obj: MixtureMaterial):
        return obj.material_fk.price_per_kilo

    def get_total_price(self, obj: MixtureMaterial):
        return obj.quantity_used * obj.material_fk.buy_price_per_kilo

    def get_total_profit(self, obj: MixtureMaterial):
        return obj.quantity_used * obj.material_fk.proft


class MixtureInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mixtures
        fields = [
            "id",
            "materials_used_cost",
            "manufacturing_cost",
            "profit",
            "selling_price",
        ]
