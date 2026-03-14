from rest_framework.serializers import ModelSerializer
from .. import models


class InvoicesSerializer(ModelSerializer):
    class Meta:
        model = models.Invoice
        fields = "__all__"


class InvoiceMaterialsSerializer(ModelSerializer):
    class Meta:
        model = models.SegmentalInvoiceMaterials
        fields = [
            "invoice",
            "material",
            "quantity_in_unit",
        ]
        extra_kwargs = {"invoice": {"required": False}, "material": {"required": False}}
