from .. import models
from apps.Material_Warehouse.models import MaterialWarehouse

# from rest_framework.request import Request
from cacheops import cached_as
from rest_framework.exceptions import NotFound


def get_mixtures(name):

    # Create a cache key based on the query parameters
    cache_key = f"transactions_{name}"

    # Use cached_as to cache the queryset
    @cached_as(models.Mixtures, extra=cache_key, timeout=3600)
    def _get_mixtures():
        if name:
            return models.Mixtures.objects.filter(name__icontains=name)
        return models.Mixtures.objects.all()

    result = _get_mixtures()
    return result


def check_if_name_available(name: str) -> bool:
    return not models.Mixtures.objects.filter(name=name).exists()


def get_specific_mixture_instance(id: int):
    try:
        return models.Mixtures.objects.get(id=id)
    except models.Mixtures.DoesNotExist:
        raise NotFound("هذه الخلطه غير موجودة")


def get_mixture_materials(mixture_id: int):
    return models.MixtureMaterial.objects.filter(mixture_fk=mixture_id)


def get_specific_material_instance(material_name: str):
    try:
        return MaterialWarehouse.objects.get(material_name=material_name)
    except MaterialWarehouse.DoesNotExist:
        raise NotFound("هذا المادة غير موجود")


def get_specific_mixture_material_instance(material_id: int):
    try:
        return models.MixtureMaterial.objects.get(id=material_id)
    except models.MixtureMaterial.DoesNotExist:
        raise NotFound("هذا المادة غير موجود")


def check_if_matrial_in_mixture(mixture_instance, material_instance):
    return models.MixtureMaterial.objects.filter(
        mixture_fk=mixture_instance, material_fk=material_instance
    ).exists()
