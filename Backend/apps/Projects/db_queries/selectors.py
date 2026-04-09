from .. import models

from rest_framework.request import Request
from rest_framework.exceptions import NotFound
from cacheops import cached_as

from apps.Clients.models import ClientProjectBalance, Client


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


def get_specific_project_using_CBP(CBP_id) -> models.RentProjects:
    try:
        return models.RentProjects.objects.get(CPB_fk=CBP_id)
    except models.RentProjects.DoesNotExist:
        raise NotFound("Project not found")


def get_r_contract_instnace(contract_id):
    try:
        return models.RentProjectContracts.objects.get(id=contract_id)
    except models.RentProjectContracts.DoesNotExist:
        raise NotFound("Contract not found")


def get_specific_project_using_id(project_id) -> models.RentProjects:
    try:
        return models.RentProjects.objects.get(id=project_id)
    except models.RentProjects.DoesNotExist:
        raise NotFound("Project not found")


def get_client_instnce(client_id):
    try:
        return Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        raise NotFound("Client not found")


def get_CBP(id):
    try:
        return ClientProjectBalance.objects.get(id=id)
    except ClientProjectBalance.DoesNotExist:
        raise NotFound("Client Project Balance not found")
