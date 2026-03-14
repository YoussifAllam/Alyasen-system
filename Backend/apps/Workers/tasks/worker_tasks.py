from ..models import (
    Workers,
    WorkerDeduction,
    WorkerAbsence,
    WorkerAdvance,
    WorkersPaidSalary,
    WorkerAlternatives,
)
from ..db_queries import services, selectors

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log

from django.utils.timezone import now
from rest_framework.exceptions import ValidationError


def update_worker_total_days_of_absence(
    worker_instance: Workers, tranaction_type: str, user_name: str
) -> tuple[int, int]:

    if tranaction_type == "أضافة":
        worker_instance.total_days_of_absence += 1
        tranaction = f"تم {tranaction_type} يوم غياب للموظف: {worker_instance.name}"
        create_transaction_log.delay(transaction_data=tranaction, username=user_name)

    elif tranaction_type == "حذف":
        worker_instance.total_days_of_absence -= 1

    worker_instance.save()
    update_worker_balance(worker_instance)


def update_worker_deduction_balance(
    worker_instance: Workers, tranaction_type: str, user_name: str, deduction_amount: float
) -> None:
    if tranaction_type == "أضافة":
        worker_instance.total_deduction += deduction_amount

    elif tranaction_type == "حذف":
        worker_instance.total_deduction -= deduction_amount

    worker_instance.save()
    update_worker_balance(worker_instance)

    tranaction = f"تم {tranaction_type} خصم للموظف: {worker_instance.name} بقيمة {deduction_amount}"
    create_transaction_log.delay(transaction_data=tranaction, username=user_name)


def update_worker_advance_balance(
    worker_instance: Workers, tranaction_type: str, user_name: str, advance_amount: float
) -> None:
    if tranaction_type == "أضافة":
        worker_instance.total_advance += advance_amount

    elif tranaction_type == "حذف":
        worker_instance.total_advance -= advance_amount

    worker_instance.save()
    update_worker_balance(worker_instance)

    tranaction = f"تم {tranaction_type} سلفة للموظف: {worker_instance.name} بقيمة {advance_amount}"
    create_transaction_log.delay(transaction_data=tranaction, username=user_name)


def update_worker_attendance(worker_instance: Workers, transaction):
    if transaction == "in":
        if selectors.has_attendance_today(worker_instance):
            raise ValidationError("لقد تم تسجيل حضور لهذا العامل اليوم بالفعل")
        worker_instance.total_days_of_work += 1
        worker_instance.save()
        services.create_in_attendance_instance_for_worker(worker_instance)
        update_worker_balance(worker_instance)

    elif transaction == "out":
        worker_attendance_instance = selectors.get_worker_attendance_instance(worker_instance)
        worker_attendance_instance.exit_date = now()
        worker_attendance_instance.save()


def update_worker_balance(worker_instance: Workers) -> float:
    worker_instance.remaining_salary = (
        (worker_instance.daily_salary * worker_instance.total_days_of_work)
        + (worker_instance.total_alternatives_amount)
        - (worker_instance.total_advance + worker_instance.total_deduction)
    )
    worker_instance.save()


def check_if_absence_date_is_valid(absence_date: str, worker_instance: Workers) -> bool:
    if absence_date < worker_instance.work_start_date:
        return False

    today = now().date()
    if absence_date > today:
        return False

    return True


def finish_worker_shift(worker_instance: Workers):
    worker_instance.total_days_of_absence = 0
    worker_instance.total_days_of_work = 0
    worker_instance.total_advance = 0
    worker_instance.total_deduction = 0
    worker_instance.total_alternatives_amount = 0
    services.create_workers_paid_salary_instance(
        worker_instance, now().date(), worker_instance.remaining_salary, None
    )
    worker_instance.remaining_salary = 0
    worker_instance.work_start_date = now().date()
    worker_instance.save()
    delete_worker_related_Data(worker_instance)


def delete_worker_related_Data(worker_instance: Workers) -> None:
    WorkersPaidSalary.objects.filter(worker=worker_instance).update(advance=None)
    WorkerAdvance.objects.filter(worker=worker_instance).delete()
    WorkerDeduction.objects.filter(worker=worker_instance).delete()
    WorkerAbsence.objects.filter(worker=worker_instance).delete()
    WorkerAlternatives.objects.filter(worker=worker_instance).delete()


def update_worker_alternative_balance(
    worker_instance: Workers, tranaction_type: str, user_name: str, alternative_amount: float
) -> None:
    if tranaction_type == "أضافة":
        worker_instance.total_alternatives_amount += alternative_amount

    elif tranaction_type == "حذف":
        worker_instance.total_alternatives_amount -= alternative_amount

    worker_instance.save()
    update_worker_balance(worker_instance)

    tranaction = f"تم {tranaction_type} مبلغ بدل للموظف: {worker_instance.name} بقيمة {alternative_amount}"
    create_transaction_log.delay(transaction_data=tranaction, username=user_name)
