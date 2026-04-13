from ..models import SupplierInvoice, InvoiceMaterial, MaterialSupplier
from ..tasks import celery_tasks


def increase_invoice_total_amount(
    invoice_instance: SupplierInvoice, material_instance: InvoiceMaterial
):
    invoice_instance.invoice_total_amount += material_instance.total_buy_price
    invoice_instance.total_amount_payable = invoice_instance.invoice_total_amount
    invoice_instance.save()
    return invoice_instance.invoice_total_amount


def decrease_invoice_total_amount(
    invoice_instance: SupplierInvoice, material_total_buy_price: float
):
    invoice_instance.invoice_total_amount -= material_total_buy_price
    invoice_instance.total_amount_payable = invoice_instance.invoice_total_amount
    invoice_instance.save()
    return invoice_instance.invoice_total_amount


def update_supplier_balance(
    invoice_total_amount: float, paid_amount: float, supplier_instance: MaterialSupplier
):
    supplier_instance.total_amount_due += invoice_total_amount
    supplier_instance.total_amount_payable += invoice_total_amount - paid_amount
    supplier_instance.total_paid_amount += paid_amount
    supplier_instance.save()

    celery_tasks.create_material_supplier_payment_record.delay(
        supplier_instance.id, paid_amount, ""
    )


def pay_for_supplier(SupplierInstance: MaterialSupplier, payment_amount: float):
    SupplierInstance.total_paid_amount += payment_amount
    SupplierInstance.total_amount_payable -= payment_amount
    SupplierInstance.save()


def add_invoice_to_supplier(invoice_instance: SupplierInvoice):
    supplier_instance = invoice_instance.supplier
    supplier_instance.total_amount_due += invoice_instance.invoice_total_amount
    supplier_instance.total_amount_payable += invoice_instance.invoice_total_amount
    supplier_instance.save()
