from ..models import WorkersPaidSalary, Attendance
from django.utils.timezone import now


def create_workers_paid_salary_instance(worker, paid_date, paid_amount, advance_instance):
    return WorkersPaidSalary.objects.create(
        worker=worker, paid_date=paid_date, paid_amount=paid_amount, advance=advance_instance
    )


def delete_workers_paid_salary_instance(advance_id):
    WorkersPaidSalary.objects.filter(advance=advance_id).delete()


def create_in_attendance_instance_for_worker(worker_instance):
    Attendance.objects.create(worker=worker_instance, enter_date=now())
