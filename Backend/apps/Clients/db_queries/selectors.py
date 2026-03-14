from rest_framework.request import Request
from cacheops import cached_as
from django.db.models import Q
from rest_framework.exceptions import NotFound

from ..models import Client, ClientInvoice, InvoicePayment, InvoiceMaterials

from apps.Mixtures.models import Mixtures
from apps.Material_Warehouse.models import MaterialWarehouse


def get_clients(request: Request):
    search_query = request.GET.get("q")

    # Create a cache key based on the query parameters
    cache_key = f"transactions_{search_query}"

    # Use cached_as to cache the queryset
    @cached_as(Client, extra=cache_key, timeout=3600)
    def _get_filtered_transactions():

        if search_query:
            return Client.objects.filter(Q(name__icontains=search_query) | Q(phone__icontains=search_query))

        return Client.objects.all()

    result = _get_filtered_transactions()
    return result


def get_client_instance(client_id: int) -> Client:
    try:
        return Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        raise NotFound({"الخطأ": "لا يوجد عميل بهذا الكود"})


def get_client_invoices_instance(client_id: int) -> ClientInvoice:
    return ClientInvoice.objects.filter(client_id=client_id)


def get_invoices_instance(invoice_num: str) -> ClientInvoice:
    try:
        return ClientInvoice.objects.get(invoice_number=invoice_num)
    except ClientInvoice.DoesNotExist:
        raise NotFound({"الخطأ": "لا توجد فاتورة بهذا الرقم"})


def get_client_payments_instances(client_id: int):
    return InvoicePayment.objects.filter(client_fk__id=client_id)


def check_if_invoice_has_this_m(invoice_num, material_instnace: MaterialWarehouse) -> bool:

    return InvoiceMaterials.objects.filter(
        invoice__invoice_number=invoice_num, material__material_name=material_instnace.material_name
    ).exists()


def get_specific_invoice_mixture_instance(mixture_id) -> InvoiceMaterials:
    try:
        return InvoiceMaterials.objects.get(id=mixture_id)
    except InvoiceMaterials.DoesNotExist:
        raise NotFound({"الخطاء": " لا يوجد خلطة بهذا الكود داخل الفاتورة"})


def get_specific_material_instance(id) -> MaterialWarehouse:
    try:
        return MaterialWarehouse.objects.get(id=id)
    except MaterialWarehouse.DoesNotExist:
        raise NotFound({"الخطاء": " لا يوجد صنف بهذا الكود "})




def get_invoice_mixtures_instances(invoice_num: str) -> InvoiceMaterials:
    return InvoiceMaterials.objects.filter(invoice__invoice_number=invoice_num)
