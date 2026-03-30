from rest_framework import serializers
from ..models import CompanyAssets, CompanyAssetsAttachments


class CompanyAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAssets
        fields = "__all__"


class CompanyAssetsAttachmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAssetsAttachments
        fields = "__all__"
