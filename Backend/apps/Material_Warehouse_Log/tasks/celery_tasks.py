from celery import shared_task
from django.utils.timezone import localdate

from .. import models


@shared_task(name="create_material_transaction_log")
def create_Material_transaction_log(
    material_name: str,
    transaction: str,
    quantity_before: float,
    quantity_after: float,
    driver_name: str = None,
    car_plate_number: str = None,
):
    transaction_date = localdate()
    models.MaterialWarehouseLog.objects.create(
        material_name=material_name,
        transaction=transaction,
        transaction_date=transaction_date,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        driver_name=driver_name,
        car_plate_number=car_plate_number,
    )
