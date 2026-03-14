from celery import shared_task
from django.utils.timezone import localdate

from .. import models


@shared_task(name="create_client_payment_invoice_record")
def create_client_payment_invoice_record(client_id: int, payment_amount: int, notes: str):
    today = localdate()
    client_instance = models.Client.objects.get(id=client_id)

    models.InvoicePayment.objects.create(
        client_fk=client_instance, payment_amount=payment_amount, payment_date=today, notes=notes
    )
