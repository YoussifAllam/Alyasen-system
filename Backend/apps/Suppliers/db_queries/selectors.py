from rest_framework.request import Request
from cacheops import cached_as
from django.db.models import Q
from rest_framework.exceptions import NotFound

from ..models import Supplier, InvoicePayment, SupplierProjectBalance


def get_suppliers(request: Request):
    search_query = request.GET.get("q")

    # Create a cache key based on the query parameters
    cache_key = f"transactions_{search_query}"

    # Use cached_as to cache the queryset
    @cached_as(Supplier, extra=cache_key, timeout=3600)
    def _get_filtered_transactions():

        if search_query:
            return Supplier.objects.filter(
                Q(name__icontains=search_query) | Q(phone__icontains=search_query)
            )

        return Supplier.objects.all()

    result = _get_filtered_transactions()
    return result


def get_supplier_instance(supplier_id: int) -> Supplier:
    try:
        return Supplier.objects.get(id=supplier_id)
    except Supplier.DoesNotExist:
        raise NotFound({"الخطأ": "لا يوجد مورد بهذا الكود"})


def get_supplier_payments_instances(supplier_id: int):
    return InvoicePayment.objects.filter(supplier_fk=supplier_id)


def get_supplier_projects(supplier_id: int):
    return SupplierProjectBalance.objects.filter(supplier_fk=supplier_id)
