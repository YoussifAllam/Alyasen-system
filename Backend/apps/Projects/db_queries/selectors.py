from .. import models
from rest_framework.request import Request
from cacheops import cached_as


def get_projects(request: Request):
    q = request.GET.get("q")
    if q:
        return models.BaseProject.objects.filter(name__icontains=q)

    return models.BaseProject.objects.all()
