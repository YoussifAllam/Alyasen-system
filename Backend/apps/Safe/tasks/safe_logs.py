from ..models import SafeLogs
from celery import shared_task


@shared_task(name="create_safe_log")
def add_safe_log(transaction: str):
    SafeLogs.objects.create(trnasaction=transaction)
