from rest_framework import serializers
from ..models import Quotations, QuotationsAttachments


class QuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quotations
        fields = "__all__"


class QuotationAttachmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationsAttachments
        fields = "__all__"
