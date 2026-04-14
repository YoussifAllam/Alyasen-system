from django.utils.timezone import localdate
from apps.Projects.models.industrial_projects_models import (
    SellingIndustrialProjectGuaranteeCheques,
)
from apps.Projects.models.rent_projects_models import RentProjectsGuaranteeCheques


def get_nearest_guarantee_checks():
    today = localdate()

    # Query future and today's cheques
    ind_checks = SellingIndustrialProjectGuaranteeCheques.objects.filter(
        cheque_date__gte=today
    ).order_by("cheque_date")

    rent_checks = RentProjectsGuaranteeCheques.objects.filter(
        cheque_date__gte=today
    ).order_by("cheque_date")

    data = []

    for check in ind_checks:
        data.append(
            {
                "client_name": check.project.CPB_fk.client_fk.name,
                "project_name": check.project.CPB_fk.project_name,
                "date": check.cheque_date.isoformat(),
                "amount": check.cheque_amount,
                "type": "selling_industrial",
            }
        )

    for check in rent_checks:
        data.append(
            {
                "client_name": check.project.CPB_fk.client_fk.name,
                "project_name": check.project.CPB_fk.project_name,
                "date": check.cheque_date.isoformat(),
                "amount": check.cheque_amount,
                "type": "rent",
            }
        )

    # Sort combined data by date ascending
    data.sort(key=lambda x: x["date"])

    # Return top 5 closest upcoming cheques
    return data[:5]
