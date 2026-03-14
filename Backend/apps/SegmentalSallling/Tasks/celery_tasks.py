# from celery import shared_task
# from django.utils.timezone import localdate

# from .. import models
# from ..db_queries import selectors


# @shared_task(name="create_client_payment_invoice_record")
# def create_client_payment_invoice_record(invoice_num: str, payment_amount: int, notes: str):
#     today = localdate()
#     invoice_instance = selectors.get_invoices_instance(invoice_num)

#     models.InvoicePayment.objects.create(
#         invoice=invoice_instance, payment_amount=payment_amount, payment_date=today, notes=notes
#     )
