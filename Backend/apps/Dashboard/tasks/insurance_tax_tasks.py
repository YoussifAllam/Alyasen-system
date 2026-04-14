from apps.Projects.models import industrial_projects_models, rent_projects_models
from apps.Projects.serializers.OutputSerializers import (
    RentProjectInfoSerializer,
    SellingIndustrialProjectDetailsSerializer,
)


def get_upcoming_insurance_tax_projects():
    # Fetch Selling Industrial Projects
    ind_projects = (
        industrial_projects_models.SellingIndustrialProjectDetails.objects.filter(
            insurance_tax_cleared=False,
            insurance_tax_date__isnull=False,
        ).order_by("insurance_tax_date")
    )
    ind_serialized = SellingIndustrialProjectDetailsSerializer(
        ind_projects[:2], many=True
    ).data

    # Fetch Rent Projects
    rent_projects = rent_projects_models.RentProjects.objects.filter(
        insurance_tax_cleared=False,
        insurance_tax_date__isnull=False,
    ).order_by("insurance_tax_date")
    rent_serialized = RentProjectInfoSerializer(rent_projects[:2], many=True).data

    return {"selling_industrial": ind_serialized, "rent": rent_serialized}
