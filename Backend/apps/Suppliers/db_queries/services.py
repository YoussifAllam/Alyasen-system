from ..models import Supplier, InvoicePayment
from ..tasks import celery_tasks


def update_supplier_balance(
    invoice_total_amount: float, paid_amount: float, supplier_instance: Supplier
):
    supplier_instance.total_amount_due += invoice_total_amount
    supplier_instance.total_amount_payable += invoice_total_amount - paid_amount
    supplier_instance.total_paid_amount += paid_amount
    supplier_instance.save()

    celery_tasks.create_supplier_payment_record.delay(
        supplier_instance.id, paid_amount, ""
    )


def pay_for_supplier(SupplierInstance: Supplier, payment_amount: float):
    SupplierInstance.total_paid_amount += payment_amount
    SupplierInstance.total_amount_payable -= payment_amount
    SupplierInstance.save()
