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


class AddNewMaterialSerializer(Serializer):
    material_name = CharField(max_length=100)
    quantity_in_unit = FloatField()
    unit = CharField()

    def validate(self, data):
        if selectors.check_material_exists(data["material_name"]):
            raise ValidationError("Material already exists")
        if data["quantity_in_unit"] < 0:
            raise ValidationError("quantity_in_kilo must be a positive number")
        return data


class MatrerialNameSerializer(Serializer):
    material_name = CharField(max_length=100)


class FillMatrerialSerializer(Serializer):
    source_material_name = CharField(required=True)
    target_material_name = CharField(required=True)
    source_qty = FloatField(required=True)
    target_added_qty = FloatField(required=True)
