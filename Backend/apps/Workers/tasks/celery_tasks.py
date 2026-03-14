# from celery import shared_task

# from ..db_queries import selectors
# from .worker_tasks import update_worker_total_days_of_absence


# @shared_task(name="update_attendence_days_to_workers")
# def update_attendence_days_to_workers():
#     workers_instances = selectors.get_workers()

#     for worker_instance in workers_instances:
#         if not worker_instance.is_in_vacation:
#             update_worker_total_days_of_absence(worker_instance, "أضافة", "النظام")
