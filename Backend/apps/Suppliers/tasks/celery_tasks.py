from celery import shared_task
from django.utils.timezone import localdate

from .. import models
from ..db_queries import selectors


@shared_task(name="create_payment_invoice_record")
def create_supplier_payment_record(data: dict, portal_invoice_file):
    today = localdate()
    supplier_instance = selectors.get_supplier_instance(data["supplier_id"])
    project_instance = selectors.get_project_balance_instance(data["project_id"])

    models.ProjectPayment.objects.create(
        supplier_fk=supplier_instance,
        project_fk=project_instance,
        portal_invoice_file=portal_invoice_file,
        portal_invoice_number=data.get("portal_invoice_number"),
        payment_amount=data["payment_amount"],
        payment_date=today,
        notes=data.get("notes", "None"),
    )
