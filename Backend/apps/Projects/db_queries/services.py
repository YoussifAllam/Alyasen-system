from apps.Suppliers.models import Supplier
from django.db.models import F


def update_supplier_balance(request):
    supplier_id = request.data.get("supplier", None)
    cost = float(request.data.get("cost"))
    if supplier_id:
        supplier = Supplier.objects.get(id=supplier_id)
        supplier.total_amount_due += cost
        supplier.save()
