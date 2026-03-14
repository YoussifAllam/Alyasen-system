from apps.Material_Warehouse.models import MaterialWarehouse
from apps.Material_Warehouse_Log.tasks.celery_tasks import create_Material_transaction_log

from ..models import ClientInvoice, InvoiceMaterials

from django.db import transaction


def check_material_availability(material_instnace: MaterialWarehouse, req_qty_of_material: float):
    """
    Check if there are enough materials in warehouse to create the required quantity of mixture

    Args:
        mixture_id: ID of the mixture to check
        required_quantity: Quantity of mixture needed

    Returns:
        tuple: (is_available: bool, message: str, missing_materials: list)
    """

    if material_instnace.quantity_in_unit < req_qty_of_material:
        return False, (f"لم تعد الكمية كافية من الصنف {material_instnace.material_name}")
    else:
        return True, " "



def create_material_production_from_invoice(invoice_instance: ClientInvoice):
    """
    Create mixture production for all mixtures in an invoice by deducting materials from warehouse

    Args:
        invoice_instance: The client invoice instance

    Returns:
        tuple: (success: bool, message: str)
    """
    with transaction.atomic():
        # Get all invoice mixtures
        invoice_materials = InvoiceMaterials.objects.select_related("material").filter(
            invoice=invoice_instance
        )

        if not invoice_materials.exists():
            return False, "لا توجد منتجات في الفاتورة"

        # First, verify availability for all mixtures
        for invoice_material in invoice_materials:
            material = invoice_material.material
            quantity_to_produce = invoice_material.quantity_in_unit
            available_quantity = material.quantity_in_unit

            if available_quantity < quantity_to_produce:
                return False, f"لا توجد كمية كافية في المخزن من ال {material.material_name}"

            material.quantity_in_unit -= quantity_to_produce
            material.save()

            create_Material_transaction_log.delay(
                material_name=material.material_name,
                transaction=f"خروج من المخزن   للفاتورة {invoice_instance.invoice_number}",  # noqa
                quantity_before=available_quantity,
                quantity_after=material.quantity_in_unit,
            )

        # Mark invoice as moved to warehouse
        invoice_instance.save()

        return True, f"تم إنشاء جميع خلطات الفاتورة {invoice_instance.invoice_number} بنجاح"