from rest_framework.serializers import ModelSerializer, ImageField, ValidationError
from .. import models


class MachineSerializer(ModelSerializer):

    class Meta:
        model = models.CompanyAssets
        fields = (
            "name",
            "price",
        )
