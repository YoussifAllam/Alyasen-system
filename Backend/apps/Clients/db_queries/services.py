from ..models import Client, ClientProjectBalance

from apps.Safe.models import Safe
from apps.Safe.tasks.safe_logs import add_safe_log
from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


def increase_safe_balance(amount: float, client_name: str):
    safe_instance, created = Safe.objects.get_or_create(id=1)
    safe_instance.balance -= amount
    safe_instance.save()
    add_safe_log.delay(transaction=f" تم سحب دفعه للمورد {client_name} بمبلغ {amount}")


# def update_client_balance(
#     invoice_total_amount: float, paid_amount: float, client_instance: Client
# ):
#     client_instance.total_amount_due += invoice_total_amount
#     client_instance.total_amount_payable += invoice_total_amount - paid_amount
#     client_instance.total_paid_amount += paid_amount
#     client_instance.save()

#     celery_tasks.create_supplier_payment_record.delay(
#         client_instance.id, paid_amount, ""
#     )


def client_payment(client_instance: Client, payment_amount: float, username: str):
    client_instance.total_paid_amount += payment_amount
    client_instance.total_amount_payable -= payment_amount
    client_instance.save()

    increase_safe_balance(payment_amount, client_instance.name)
    create_transaction_log.delay(
        username=username,
        transaction_data=f"تم تحصيل دفعه من العميل {client_instance.name} بمبلغ {payment_amount}",
    )


def update_project_balance(
    project_instance: ClientProjectBalance, payment_amount: float
):
    project_instance.paid += payment_amount
    project_instance.remining -= payment_amount
    project_instance.save()
