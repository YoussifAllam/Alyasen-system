from rest_framework import serializers
from ..models import CompanyAssets


class CompanyAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyAssets
        fields = "__all__"
