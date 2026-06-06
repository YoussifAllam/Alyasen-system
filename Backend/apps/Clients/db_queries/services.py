from ..models import Client, ClientProjectBalance
from . import selectors

from apps.Safe.db_queries.services import adjust_safe_balance
from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log

from apps.Projects.models import rent_projects_models, industrial_projects_models


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


def client_payment(client_id: int, payment_amount: float, username: str):
    client_instance = selectors.get_client_instance(client_id)
    client_instance.total_paid_amount += payment_amount
    client_instance.total_remaining_balance_owed_to_us -= payment_amount
    client_instance.save()

    adjust_safe_balance(
        process="add",
        amount=payment_amount,
        note=f"تم تحصيل دفعه من العميل {client_instance.name}",
        username=username,
    )
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


def create_CPB_instance(
    client_instance,
    campaine_instance=None,
    base_project_instance=None,
):
    if campaine_instance:
        CPB_instance = ClientProjectBalance.objects.create(
            client_fk=client_instance,
            campaine_fk=campaine_instance,
            project_type="campaine",
            total=campaine_instance.total_cost,
            paid=0,
            remining=campaine_instance.total_cost,
        )
    else:
        CPB_instance = ClientProjectBalance.objects.create(
            client_fk=client_instance,
            project_fk=base_project_instance,
            project_type="project",
            total=base_project_instance.cost,
            paid=0,
            remining=base_project_instance.cost,
        )

    return CPB_instance


def create_rent_p_instnace(CBP_instance, buying_price):
    rent_projects_models.RentProjects.objects.create(
        CPB_fk=CBP_instance,
        buying_price=buying_price,
    )


def update_client_balance_using_CBP(CBP_instance, client_instance, user_name):
    client_instance.total_balance_owed_to_us += CBP_instance.total
    client_instance.total_remaining_balance_owed_to_us += CBP_instance.total
    client_instance.save()

    create_transaction_log.delay(
        username=user_name,
        transaction_data=f"تم اضافه مشروع جديد للعميل {client_instance.name}",
    )


def create_sell_ind_p_instnace(CBP_instance, buying_price):
    industrial_projects_models.SellingIndustrialProjectDetails.objects.create(
        CPB_fk=CBP_instance,
        buying_price=buying_price,
    )
