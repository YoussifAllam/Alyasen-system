from cacheops import cached_as
from rest_framework.exceptions import NotFound

from ..models import Invoice, SegmentalInvoiceMaterials

from apps.Material_Warehouse.models import MaterialWarehouse


def get_invoice_instances():
    # Build cache key from non-None parameters
    cache_key = "invoice__"

    @cached_as(Invoice, extra=cache_key, timeout=3600)
    def _get_cached_query():
        # Build the query
        return Invoice.objects.all()

    return _get_cached_query()


def get_specific_invoice_instance(invoice_num: str) -> Invoice:
    try:
        return Invoice.objects.get(invoice_number=invoice_num)
    except Invoice.DoesNotExist:
        raise NotFound({"الخطأ": "لا توجد فاتورة بهذا الرقم"})


def check_if_invoice_has_this_m(invoice_num, material_instnace: MaterialWarehouse) -> bool:

    return SegmentalInvoiceMaterials.objects.filter(
        invoice__invoice_number=invoice_num, material__material_name=material_instnace.material_name
    ).exists()


def get_specific_segmental_material_instance(material_id: int) -> SegmentalInvoiceMaterials:
    try:
        return SegmentalInvoiceMaterials.objects.get(id=material_id)
    except SegmentalInvoiceMaterials.DoesNotExist:
        raise NotFound({"الخطاء": "  لا يوجد منتج بهذا الكود داخل الفاتورة"})


def get_specific_material_instance(material_id: int) -> MaterialWarehouse:
    try:
        return MaterialWarehouse.objects.get(id=material_id)
    except MaterialWarehouse.DoesNotExist:
        raise NotFound({"الخطاء": " لا يوجد خلطة بهذا الكود "})


def get_invoice_materials_instances(invoice_num: str) -> SegmentalInvoiceMaterials:
    return SegmentalInvoiceMaterials.objects.filter(invoice__invoice_number=invoice_num)
