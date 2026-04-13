from ..models import industrial_projects_models


def increase_project_materials_cost(CBP_id, amount):
    project = industrial_projects_models.SellingIndustrialProjectDetails.objects.get(
        CPB_fk__id=CBP_id
    )
    project.total_materials_cost += amount
    project.save()
