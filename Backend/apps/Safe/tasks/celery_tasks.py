from ..models import Safe
from celery import shared_task

from .safe_logs import add_safe_log

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


@shared_task(name="reduce_safe_balance")
def reduce_safe_balance(amount: float, transaction: str, username: str):
    safe = Safe.objects.first()
    safe.balance -= amount
    safe.save()

    add_safe_log.delay(transaction)
    create_transaction_log.delay(transaction_data=transaction, username=username)


@shared_task(name="add_safe_balance")
def increase_safe_balance(amount: float, transaction: str, username: str):
    safe = Safe.objects.first()
    safe.balance += amount
    safe.save()

    add_safe_log.delay(transaction)
    create_transaction_log.delay(transaction_data=transaction, username=username)
