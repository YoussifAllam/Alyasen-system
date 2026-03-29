from apps.Suppliers.models import Supplier

from ..models.base_project_models import BaseProject

from django.db.models import F


def update_supplier_balance(request):
    supplier_id = request.data.get("supplier", None)
    cost = float(request.data.get("cost"))
    if supplier_id:
        supplier = Supplier.objects.get(id=supplier_id)
        supplier.total_amount_due += cost
        supplier.save()


def update_project_status(project: BaseProject):
    cur_status = project.project_status
    if cur_status == "active":
        project.project_status = "inactive"
    else:
        project.project_status = "active"
    project.save()
