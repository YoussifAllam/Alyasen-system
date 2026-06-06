from ..models import Supplier, ProjectPayment, SupplierProjectBalance
from ..tasks import celery_tasks

from apps.Safe.db_queries.services import adjust_safe_balance


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

    adjust_safe_balance(
        process="subtract",
        amount=payment_amount,
        note=f"تم سحب دفعه للمورد {SupplierInstance.name}",
    )


def pay_for_project(project_instance: SupplierProjectBalance, payment_amount: float):
    project_instance.paid += payment_amount
    project_instance.remining -= payment_amount
    project_instance.save()
