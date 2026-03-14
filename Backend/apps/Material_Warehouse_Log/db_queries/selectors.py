from .. import models
from rest_framework.request import Request
from cacheops import cached_as
from django.utils.timezone import localdate


def get_warehouse_transactions(request: Request):
    material_name = request.GET.get("material_name")
    transaction_date = request.GET.get("transaction_date")

    # Create a cache key based on the query parameters
    cache_key = f"transactions_{material_name}_{transaction_date}"

    # Use cached_as to cache the queryset
    @cached_as(models.MaterialWarehouseLog, extra=cache_key, timeout=3600)
    def _get_filtered_transactions():

        if material_name and not transaction_date:
            return models.MaterialWarehouseLog.objects.filter(material_name=material_name)

        if transaction_date and not material_name:
            return models.MaterialWarehouseLog.objects.filter(transaction_date=transaction_date)

        if transaction_date and material_name:
            return models.MaterialWarehouseLog.objects.filter(
                transaction_date=transaction_date, material_name=material_name
            )

        return models.MaterialWarehouseLog.objects.all()

    result = _get_filtered_transactions()
    return result


def get_warehouse_today_transactions(request: Request):
    today = localdate()
    # Create a cache key based on the query parameters
    cache_key = f"transactions_{today}"

    # Use cached_as to cache the queryset
    @cached_as(models.MaterialWarehouseLog, extra=cache_key, timeout=3600)
    def _get_filtered_today_transactions():
        return models.MaterialWarehouseLog.objects.filter(transaction_date=today)

    result = _get_filtered_today_transactions()
    return result
