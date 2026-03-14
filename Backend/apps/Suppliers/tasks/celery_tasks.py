from celery import shared_task
from django.utils.timezone import localdate

from .. import models
from ..db_queries import selectors


@shared_task(name="create_payment_invoice_record")
def create_supplier_payment_record(supplier_id: str, payment_amount: int, notes: str):
    today = localdate()
    supplier_instance = selectors.get_supplier_instance(supplier_id)

    models.InvoicePayment.objects.create(
        supplier_fk=supplier_instance, payment_amount=payment_amount, payment_date=today, notes=notes
    )
