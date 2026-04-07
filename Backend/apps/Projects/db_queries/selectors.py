from .. import models

from rest_framework.request import Request
from rest_framework.exceptions import NotFound
from cacheops import cached_as


def get_projects(request: Request):
    q = request.GET.get("q")
    if q:
        return models.BaseProject.objects.filter(name__icontains=q)

    return models.BaseProject.objects.all()


def get_base_project_by_id(id):
    try:
        return models.BaseProject.objects.get(id=id)
    except models.BaseProject.DoesNotExist:
        raise NotFound("Project not found")


def get_specific_project(project_id):
    try:
        return models.RentProjects.objects.get(project_id=id)
    except models.RentProjects.DoesNotExist:
        raise NotFound("Project not found")
