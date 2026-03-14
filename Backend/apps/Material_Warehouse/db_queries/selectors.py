from .. import models
from cacheops import cached_as
from rest_framework.exceptions import ValidationError


def get_materials():

    # Create a cache key based on the query parameters
    cache_key = "transactions"

    # Use cached_as to cache the queryset
    @cached_as(models.MaterialWarehouse, extra=cache_key, timeout=3600)
    def _get_filtered_transactions():
        return models.MaterialWarehouse.objects.all()

    result = _get_filtered_transactions()
    return result


def check_material_exists(material_name: str) -> bool:
    return models.MaterialWarehouse.objects.filter(material_name=material_name).exists()


def get_specific_material_instance(material_name: str) -> models.MaterialWarehouse:
    try:
        return models.MaterialWarehouse.objects.get(material_name=material_name)
    except models.MaterialWarehouse.DoesNotExist:
        raise ValidationError("Material does not exist")


def filter_by_name(material_name: str) -> models.MaterialWarehouse:
    return models.MaterialWarehouse.objects.filter(material_name__icontains=material_name)


def get_materials_names() -> models.MaterialWarehouse:
    return models.MaterialWarehouse.objects.all().values_list("material_name", flat=True)
