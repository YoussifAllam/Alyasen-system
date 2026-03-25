from .. import models
from rest_framework.request import Request
from cacheops import cached_as


def get_projects(request: Request):
    q = request.GET.get("q")

    cache_key = f"project_{q}_"

    @cached_as(models.BaseProject, extra=cache_key, timeout=3600)
    def _get_filtered_projects():

        if q:
            return models.BaseProject.objects.filter(
                name__icontains=q, project_status=models.ProjectStatus.active
            )

        return models.BaseProject.objects.filter(
            project_status=models.ProjectStatus.active
        )

    result = _get_filtered_projects()
    return result
