from apps.Material_Warehouse_Log.tasks.celery_tasks import create_Material_transaction_log
from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log

from ..models import MaterialWarehouse


def create_both_transaction_logs(
    material_instance: MaterialWarehouse,
    transaction,
    username,
    quantity_before: float = 0,
    driver_name: str = None,
    car_plate_number: str = None,
):

    create_Material_transaction_log.delay(
        material_instance.material_name,
        transaction,
        quantity_before,
        material_instance.quantity_in_unit,
        driver_name,
        car_plate_number,
    )

    create_transaction_log.delay(username, transaction)
