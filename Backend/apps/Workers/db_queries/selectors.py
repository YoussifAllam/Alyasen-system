from rest_framework.request import Request
from cacheops import cached_as
from django.db.models import Q
from django.utils.timezone import now
from rest_framework.exceptions import NotFound

from ..models import Workers, WorkerAbsence, WorkerAdvance, WorkerDeduction, Attendance, WorkerAlternatives


def get_workers(request: Request):
    search_query = request.GET.get("q")

    # Create a cache key based on the query parameters
    cache_key = f"workers{search_query}"

    # Use cached_as to cache the queryset
    @cached_as(Workers, extra=cache_key, timeout=3600)
    def _get_filtered_workers():

        if search_query:
            return Workers.objects.only("worker_id", "name", "phone").filter(
                Q(name__icontains=search_query) | Q(phone__icontains=search_query)
            )

        return Workers.objects.only("worker_id", "name", "phone")

    result = _get_filtered_workers()
    return result


def get_specific_worker_instance(worker_id: int) -> Workers:
    try:
        return Workers.objects.get(worker_id=worker_id)
    except Workers.DoesNotExist:
        raise NotFound({"الخطأ": "لا يوجد عامل بهذا الكود"})


def get_absences_days(worker_id):
    return WorkerAbsence.objects.filter(worker__worker_id=worker_id)


def check_if_absence_date_is_exist(absence_date):
    try:
        WorkerAbsence.objects.get(absence_date=absence_date)
        return True
    except WorkerAbsence.DoesNotExist:
        return False


def get_specific_absence_instance(absence_id: int):
    try:
        return WorkerAbsence.objects.get(id=absence_id)
    except WorkerAbsence.DoesNotExist:
        raise NotFound({"الخطاء": "لا يوجد غياب بهذا الكود"})


def get_workers_instances_without_cache() -> Workers:
    return Workers.objects.all()


def get_worker_deductions_instance(worker_id):
    return WorkerDeduction.objects.filter(worker__worker_id=worker_id)


def get_specific_deduction_instance(deduction_id):
    try:
        return WorkerDeduction.objects.get(id=deduction_id)
    except WorkerDeduction.DoesNotExist:
        raise NotFound({"الخطاء": "لا يوجد خصم بهذا الكود"})


def get_worker_sdvances_instance(worker_id):
    return WorkerAdvance.objects.filter(worker__worker_id=worker_id)


def get_specific_advance_instance(advance_id):
    try:
        return WorkerAdvance.objects.get(id=advance_id)
    except WorkerAdvance.DoesNotExist:
        raise NotFound({"الخطاء": "لا يوجد خصم بهذا الكود"})


def get_worker_attendance_instance(worker_instance):
    try:
        return Attendance.objects.get(worker=worker_instance, attendance_date=now().date())
    except Attendance.DoesNotExist:
        raise NotFound({"الخطاء": "العامل لم يحضر اليوم "})


def get_worker_all_attendance_instances(worker_id):
    return Attendance.objects.filter(worker__worker_id=worker_id)


def get_worker_alternatives_instances(worker_id):
    return WorkerAlternatives.objects.filter(worker__worker_id=worker_id)


def get_specific_alternative_instance(alternative_id) -> WorkerAlternatives:
    try:
        return WorkerAlternatives.objects.get(id=alternative_id)
    except WorkerAlternatives.DoesNotExist:
        raise NotFound({"الخطاء": "لا يوجد عملية بهذا الكود"})


def has_attendance_today(worker_instance):
    """Check if worker already has attendance record for today"""
    today = now().date()
    return Attendance.objects.filter(worker=worker_instance, attendance_date=today).exists()
