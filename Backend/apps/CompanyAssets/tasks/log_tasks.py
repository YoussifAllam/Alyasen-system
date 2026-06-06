from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


def create_user_transaction_log(transaction: str, username: str, transaction_type: str):
    create_transaction_log(
        username=username,
        transaction_data=transaction,
        transaction_type=transaction_type,
    )
