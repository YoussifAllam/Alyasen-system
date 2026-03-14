from rest_framework.serializers import ModelSerializer
from .. import models


class ExpensesSerializer(ModelSerializer):
    class Meta:
        model = models.Expenses
        fields = "__all__"
        read_only_fields = [
            "id",
        ]
