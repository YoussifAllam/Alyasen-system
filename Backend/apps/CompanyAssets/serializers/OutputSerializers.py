from rest_framework import serializers

from ..models import CompanyAssets, CompanyAssetsAttachments


class CompanyAssetsSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CompanyAssets
        fields = "__all__"


class CompanyAssetsAttachmentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAssetsAttachments
        fields = "__all__"
