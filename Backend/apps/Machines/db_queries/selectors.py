from rest_framework.request import Request
from cacheops import cached_as
from django.db.models import Q
from rest_framework.exceptions import NotFound

from ..models import Machines, MachineComponents, MachineRepairHistory


def get_Machines_instances(request: Request):
    # Get parameters with proper cleaning
    machien_name = request.GET.get("q", "").strip() or None
    print(machien_name)
    # Build cache key from non-None parameters
    cache_key = f"machine_{machien_name}"

    @cached_as(Machines, extra=cache_key, timeout=3600)
    def _get_cached_query():
        # Build the query
        query = Q()

        if machien_name:
            query &= Q(name__icontains=machien_name)
            return Machines.objects.filter(query)

        return Machines.objects.all()

    return _get_cached_query()


def get_specific_machine_instance(machine_id):
    try:
        return Machines.objects.get(id=machine_id)
    except Machines.DoesNotExist:
        raise NotFound("هذا الجهاز غير موجود")


def get_machine_components_instances(machine_id):
    return MachineComponents.objects.filter(machine=machine_id)


def get_specific_machine_component_instance(machine_component_id):
    try:
        return MachineComponents.objects.get(id=machine_component_id)
    except MachineComponents.DoesNotExist:
        raise NotFound("هذا المكون غير موجود")


def get_machine_repair_history_instances(machine_id):
    return MachineRepairHistory.objects.filter(machine=machine_id)


def get_specific_machine_repair_history_instance(machine_repair_history_id):
    try:
        return MachineRepairHistory.objects.get(id=machine_repair_history_id)
    except MachineRepairHistory.DoesNotExist:
        raise NotFound("هذا التصحيح غير موجود")
