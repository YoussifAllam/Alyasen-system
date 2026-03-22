from rest_framework import serializers
from ..models import SafeLogs


class SafeLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafeLogs
        fields = ["trnasaction", "date"]
