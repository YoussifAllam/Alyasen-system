from celery import shared_task

from ..db_queries.services import adjust_safe_balance


@shared_task(name="reduce_safe_balance")
def reduce_safe_balance(amount: float, note: str, username: str = ""):
    return adjust_safe_balance(
        process="subtract", amount=amount, note=note, username=username
    )


@shared_task(name="increase_safe_balance")
def increase_safe_balance(amount: float, note: str, username: str = ""):
    return adjust_safe_balance(
        process="add", amount=amount, note=note, username=username
    )
