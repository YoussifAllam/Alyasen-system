from rest_framework import serializers
from ..models import MaterialWarehouse


class MaterialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialWarehouse
        fields = "__all__"
