from rest_framework.serializers import Serializer
from typing import Dict, Any, TypeVar, Type, Tuple
from rest_framework.serializers import (
    ValidationError,
    CharField,
    FloatField,
    IntegerField,
)

from ..db_queries import selectors

SerializerType = TypeVar("SerializerType bound=BaseSerializer")
ResponseType = Tuple[Dict[str, Any], int]


def validate_serializer(
    serializer_class: Type[SerializerType], data: Dict
) -> SerializerType:
    """Validate serializer data with consistent error handling"""
    serializer = serializer_class(data=data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    return serializer


class InvoicePaymentSerializer(Serializer):
    supplier_id = IntegerField(required=True)
    payment_amount = FloatField(min_value=0, required=True)
