from django.db import transaction

from ..models import Safe
from ..tasks.safe_logs import add_safe_log


@transaction.atomic
def adjust_safe_balance(
    *, process: str, amount: float, note: str = "", username: str = ""
):
    if amount <= 0:
        raise ValueError("المبلغ يجب أن يكون أكبر من صفر")

    safe, _created = Safe.objects.select_for_update().get_or_create(id=1)

    if process == "add":
        safe.balance += amount
        operation_type = "deposit"
        action_label = "إيداع"
    elif process == "subtract":
        if safe.balance < amount:
            raise ValueError("رصيد الخزنة غير كافٍ لإتمام السحب")
        safe.balance -= amount
        operation_type = "withdrawal"
        action_label = "سحب"
    else:
        raise ValueError("نوع العملية غير صالح")

    safe.save()

    parts = [f"{action_label} بمبلغ {amount:,.2f} جنيه"]
    if note:
        parts.append(note)
    if username:
        parts.append(f"بواسطة {username}")
    transaction_text = " — ".join(parts)

    add_safe_log(
        transaction_text,
        amount=amount,
        operation_type=operation_type,
        balance_after=safe.balance,
    )

    return safe.balance
