from rest_framework.serializers import Serializer
from typing import Dict, Any, TypeVar, Type, Tuple
from rest_framework.serializers import ValidationError, CharField, FloatField, IntegerField

from ..db_queries import selectors

SerializerType = TypeVar("SerializerType bound=BaseSerializer")
ResponseType = Tuple[Dict[str, Any], int]


def validate_serializer(serializer_class: Type[SerializerType], data: Dict) -> SerializerType:
    """Validate serializer data with consistent error handling"""
    serializer = serializer_class(data=data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    return serializer


class InvoicePaymentSerializer(Serializer):
    client_id = IntegerField(required=True)
    payment_amount = FloatField(min_value=0, required=True)


class inviceMaterialsPSerializer(Serializer):
    invoice_num = CharField(required=True)
    material_name = CharField(required=True)
    quantity_in_kilo = FloatField(min_value=0)
    buy_price_per_kilo = FloatField(min_value=0)
    sell_price_per_kilo = FloatField(min_value=0)

    def validate(self, attrs):
        invoice_num = attrs["invoice_num"]

        material_name = attrs["material_name"]
        if selectors.check_if_invoice_has_this_m(invoice_num, material_name):
            raise ValidationError("هذه المادة  موجودة بالفعل في هذا الفاتورة")
        return attrs
