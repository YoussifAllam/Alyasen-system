from rest_framework import serializers

from ..models import SafeLogs


class SafeLogsSerializer(serializers.ModelSerializer):
    transaction = serializers.CharField(source="trnasaction")
    time = serializers.SerializerMethodField()
    operation_type_display = serializers.SerializerMethodField()

    class Meta:
        model = SafeLogs
        fields = [
            "id",
            "transaction",
            "trnasaction",
            "date",
            "time",
            "amount",
            "operation_type",
            "operation_type_display",
            "balance_after",
        ]

    def get_time(self, obj):
        if not obj.date:
            return ""
        return obj.date.strftime("%H:%M:%S")

    def get_operation_type_display(self, obj):
        labels = {
            "deposit": "إيداع",
            "withdrawal": "سحب",
            "adjustment": "تسوية",
        }
        return labels.get(obj.operation_type, "")
