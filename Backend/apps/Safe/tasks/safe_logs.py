from ..models import SafeLogs


def add_safe_log(
    transaction: str,
    *,
    amount=None,
    operation_type="",
    balance_after=None,
):
    SafeLogs.objects.create(
        trnasaction=transaction,
        amount=amount,
        operation_type=operation_type or "",
        balance_after=balance_after,
    )
