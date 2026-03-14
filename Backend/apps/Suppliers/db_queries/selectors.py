from rest_framework.request import Request
from cacheops import cached_as
from django.db.models import Q
from rest_framework.exceptions import NotFound

from ..models import Supplier, SupplierInvoice, InvoicePayment, InvoiceMaterial


def get_suppliers(request: Request):
    search_query = request.GET.get("q")

    # Create a cache key based on the query parameters
    cache_key = f"transactions_{search_query}"

    # Use cached_as to cache the queryset
    @cached_as(Supplier, extra=cache_key, timeout=3600)
    def _get_filtered_transactions():

        if search_query:
            return Supplier.objects.filter(Q(name__icontains=search_query) | Q(phone__icontains=search_query))

        return Supplier.objects.all()

    result = _get_filtered_transactions()
    return result


def get_supplier_instance(supplier_id: int) -> Supplier:
    try:
        return Supplier.objects.get(id=supplier_id)
    except Supplier.DoesNotExist:
        raise NotFound({"الخطأ": "لا يوجد مورد بهذا الكود"})


def get_supplier_invoices_instance(supplier_id: int) -> SupplierInvoice:
    return SupplierInvoice.objects.filter(supplier_id=supplier_id)


def get_invoices_instance(invoice_num: str) -> SupplierInvoice:
    try:
        return SupplierInvoice.objects.get(invoice_number=invoice_num)
    except SupplierInvoice.DoesNotExist:
        raise NotFound({"الخطأ": "لا توجد فاتورة بهذا الرقم"})


def get_supplier_payments_instances(supplier_id: int):
    return InvoicePayment.objects.filter(supplier_fk=supplier_id)


def check_if_invoice_has_this_m(invoice_num, material_name):

    return InvoiceMaterial.objects.filter(
        invoice__invoice_number=invoice_num, material_name=material_name
    ).exists()


def get_specific_invoice_materials_instance(material_id) -> InvoiceMaterial:
    try:
        return InvoiceMaterial.objects.get(id=material_id)
    except InvoiceMaterial.DoesNotExist:
        raise NotFound({"الخطاء": " لا يوجد مادة بهذا الكود داخل الفاتورة"})


def get_invoice_materials_instance(invoice_num: str) -> InvoiceMaterial:
    return InvoiceMaterial.objects.filter(invoice__invoice_number=invoice_num)
