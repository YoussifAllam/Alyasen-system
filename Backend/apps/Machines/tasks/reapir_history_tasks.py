from ..models import Machines
from datetime import datetime


def update_machein_last_repair_date(machine_instance: Machines, date: str):
    # Use the standard, cross-platform format string
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()

    if not machine_instance.last_repair_date:
        machine_instance.last_repair_date = date_obj
        machine_instance.save()

    else:
        machine_instance.last_repair_date < date_obj
        machine_instance.last_repair_date = date_obj
        machine_instance.save()
