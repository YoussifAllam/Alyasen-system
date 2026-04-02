from rest_framework.serializers import Serializer
from typing import Dict, Any, TypeVar, Type, Tuple
from rest_framework.serializers import ValidationError, BaseSerializer, DateField


SerializerType = TypeVar("SerializerType", bound=BaseSerializer)
ResponseType = Tuple[Dict[str, Any], int]


def validate_serializer(serializer_class: Type[SerializerType], data: Dict) -> SerializerType:
    """Validate serializer data with consistent error handling"""
    serializer = serializer_class(data=data)
    if not serializer.is_valid():
        raise ValidationError(serializer.errors)
    return serializer


class FilterSerializer(Serializer):
    created_date = DateField()
