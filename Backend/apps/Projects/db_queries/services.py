from apps.Suppliers.models import Supplier

from ..models import (
    base_project_models,
    rent_projects_models,
    industrial_projects_models,
)
from ..serializers import InputSerializers
from . import selectors

from django.db.models import F
from django.db.models import Sum, Q

from apps.Suppliers.models import SupplierProjectBalance
from apps.Clients.models import ClientProjectBalance, ProjectPayment, Client


def update_supplier_balance(request):
    supplier_id = request.data.get("supplier", None)
    cost = float(request.data.get("cost"))
    if supplier_id:
        supplier = Supplier.objects.get(id=supplier_id)
        supplier.total_amount_due += cost
        supplier.total_amount_payable += cost
        supplier.save()


def update_project_status(project: base_project_models.BaseProject):
    cur_status = project.project_status
    if cur_status == "active":
        project.project_status = "inactive"
    else:
        project.project_status = "active"
    project.save()


def create_supplier_project_balance_instance(
    supplier_id: int, project: base_project_models.BaseProject
):
    SupplierProjectBalance.objects.create(
        supplier_fk=supplier_id,
        project_fk=project,
        total=project.cost,
        remining=project.cost,
    )


def create_r_p_contracts(r_p_instance, attachments):
    objs_to_create = []

    for file in attachments:
        objs_to_create.append(
            rent_projects_models.RentProjectContracts(
                project=r_p_instance, contract=file
            )
        )

    rent_projects_models.RentProjectContracts.objects.bulk_create(objs_to_create)


def update_project_info(
    CBP_id: int, rent_project_instance: rent_projects_models.RentProjects
):
    CBP_instance = selectors.get_CBP(CBP_id)
    CBP_instance.total = rent_project_instance.selling_price
    CBP_instance.remining = rent_project_instance.selling_price - CBP_instance.paid
    CBP_instance.save()

    update_client_balance_fields(CBP_instance)


def calculate_client_financials(client_instance: Client) -> dict:
    """
    Calculate total, paid, and remaining balance for a client.

    - total: SUM of all ClientProjectBalance.total
    - paid: SUM of ProjectPayment.payment_amount where:
        * payment belongs to client's project balances
        * if payment_type == 'check', only include if is_cleared == True
    - remaining: total - paid
    """

    # Get all project balances for this client
    client_balances = ClientProjectBalance.objects.filter(client_fk=client_instance.id)

    # Calculate total
    total = client_balances.aggregate(total=Sum("total"))["total"] or 0

    # Calculate paid amount:
    # Include cash/other payments always, but checks only if cleared
    paid = (
        ProjectPayment.objects.filter(client_project_balance_fk__in=client_balances)
        .filter(Q(is_cleared=True))
        .aggregate(paid=Sum("payment_amount"))["paid"]
        or 0  # noqa
    )

    remaining = total - paid

    return {
        "total": total,
        "paid": paid,
        "remaining": remaining,
    }


def update_client_balance_fields(CBP_instance: ClientProjectBalance):
    """
    Calculates and saves the financial fields directly on the Client model.
    """
    client_instance = selectors.get_client_instnce(CBP_instance.client_fk.id)
    financials = calculate_client_financials(client_instance)

    client_instance.total_balance_owed_to_us = financials["total"]
    client_instance.total_paid_amount = financials["paid"]
    client_instance.total_remaining_balance_owed_to_us = financials["remaining"]
    client_instance.save(
        update_fields=[
            "total_balance_owed_to_us",
            "total_paid_amount",
            "total_remaining_balance_owed_to_us",
        ]
    )


# ______
def create_sell_ind_p_contracts(sell_ind_p_instance, attachments):
    objs_to_create = []

    for file in attachments:
        objs_to_create.append(
            industrial_projects_models.IndustrialProjectContracts(
                project=sell_ind_p_instance, contract=file
            )
        )

    industrial_projects_models.IndustrialProjectContracts.objects.bulk_create(
        objs_to_create
    )
