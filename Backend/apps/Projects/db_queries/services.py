from apps.Suppliers.models import Supplier

from ..models import base_project_models, rent_projects_models

from django.db.models import F

from apps.Suppliers.models import SupplierProjectBalance


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
