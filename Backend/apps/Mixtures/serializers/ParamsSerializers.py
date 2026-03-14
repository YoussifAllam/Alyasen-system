from rest_framework.serializers import Serializer
from typing import Dict, Any, TypeVar, Type, Tuple
from rest_framework.serializers import ValidationError, BaseSerializer, CharField, FloatField

from ..db_queries import selectors

SerializerType = TypeVar("SerializerType", bound=BaseSerializer)
ResponseType = Tuple[Dict[str, Any], int]


def validate_serializer(serializer_class: Type[SerializerType], data: Dict) -> SerializerType:
    """Validate serializer data with consistent error handling"""
    serializer = serializer_class(data=data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    return serializer


class MixtureNameSerializer(Serializer):
    name = CharField(required=True)

    def validate_name(self, value: str):
        if not selectors.check_if_name_available(value):
            raise ValidationError("هذا الأسم مستخدم من قبل")
        return value


class UpdateMixtureInfo(Serializer):
    profit = FloatField(required=True, min_value=0)
    manufacturing_cost = FloatField(required=True, min_value=0)
