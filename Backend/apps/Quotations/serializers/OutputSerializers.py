from rest_framework import serializers
from ..models import Quotations


class QuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotations
        fields = "__all__"
