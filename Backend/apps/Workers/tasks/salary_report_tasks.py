from ..models import Workers
from ..serializers import OutputSerializers
from ..db_queries import selectors


def get_worker_salary_report(worker_instance: Workers):
    basic_info = get_worker_basic_info(worker_instance=worker_instance)
    alternatives_data = get_worker_alternatives_data(worker_instance=worker_instance)
    advances_data = get_worker_advance_data(worker_instance=worker_instance)
    deductions_data = get_worker_deductions_data(worker_instance=worker_instance)

    final_data = {
        "basic_info": basic_info,
        "alternatives_data": alternatives_data,
        "advances_data": advances_data,
        "deductions_data": deductions_data,
    }

    return final_data


def get_worker_basic_info(worker_instance: Workers):
    return OutputSerializers.WorkersInfoSerializer(worker_instance, many=False).data


def get_worker_alternatives_data(worker_instance: Workers):
    worker_alternatives_instances = selectors.get_worker_alternatives_instances(
        worker_id=worker_instance.worker_id
    )
    return OutputSerializers.WorkerAlternativesSerializer(worker_alternatives_instances, many=True).data


def get_worker_advance_data(worker_instance: Workers):
    worker_advances_instances = selectors.get_worker_sdvances_instance(worker_id=worker_instance.worker_id)
    return OutputSerializers.WorkerAdvanceSerializer(worker_advances_instances, many=True).data


def get_worker_deductions_data(worker_instance: Workers):
    worker_deductions_instances = selectors.get_worker_deductions_instance(
        worker_id=worker_instance.worker_id
    )
    return OutputSerializers.WorkerDeductionsSerializer(worker_deductions_instances, many=True).data
