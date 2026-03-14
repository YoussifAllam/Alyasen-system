from rest_framework import serializers
from ..models import MaterialWarehouseLog


class WarehouseTransactionsLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialWarehouseLog
        exclude = ["id"]
