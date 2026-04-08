from rest_framework.request import Request
from cacheops import cached_as
from django.db.models import Q
from rest_framework.exceptions import NotFound

from ..models import Client, ProjectPayment, ClientProjectBalance

from apps.Projects.models import BaseProject
from apps.Campaine.models import Campaine


def get_clients(request: Request):
    search_query = request.GET.get("q")

    # Create a cache key based on the query parameters
    cache_key = f"transactions_{search_query}"

    # Use cached_as to cache the queryset
    @cached_as(Client, extra=cache_key, timeout=3600)
    def _get_filtered_transactions():

        if search_query:
            return Client.objects.filter(
                Q(name__icontains=search_query) | Q(phone__icontains=search_query)
            )

        return Client.objects.all()

    result = _get_filtered_transactions()
    return result


def get_client_instance(client_id: int) -> Client:
    try:
        return Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        raise NotFound({"الخطأ": "لا يوجد عميل بهذا الكود"})


def get_client_project_and_campaings(client_id):
    # projects = BaseProject.objects.filter(client=client_id)
    # campaigns = Campaine.objects.filter(client=client_id)
    # return projects, campaigns
    return ClientProjectBalance.objects.filter(client_fk=client_id)


def get_client_CPB(project_id: int, project_type: str):
    try:
        if project_type == "campaine":
            CPB_obj = ClientProjectBalance.objects.get(campaine_fk=project_id)
        else:
            CPB_obj = ClientProjectBalance.objects.get(project_fk=project_id)

        return CPB_obj
    except ClientProjectBalance.DoesNotExist:
        raise NotFound({"الخطأ": "لا يوجد دفعات لهذا المشروع"})


def get_client_payments_instances_by_CPB(project_id: int, project_type: str):
    try:
        if project_type == "campaine" or project_type == "حملة":
            print("campaine")
            CPB_obj = ClientProjectBalance.objects.get(campaine_fk=project_id)
        else:
            print("project")
            CPB_obj = ClientProjectBalance.objects.get(project_fk=project_id)

        return CPB_obj.payments.all()
    except ClientProjectBalance.DoesNotExist:
        raise NotFound({"الخطأ": "لا يوجد دفعات لهذا المشروع"})


def get_payment_instance(payment_id):
    try:
        return ProjectPayment.objects.get(id=payment_id)
    except ProjectPayment.DoesNotExist:
        raise NotFound({"الخطأ": "لا يوجد دفعة بهذا الكود"})


def get_campaine_instance(id) -> Campaine:
    try:
        return Campaine.objects.get(id=id)
    except Campaine.DoesNotExist:
        raise NotFound({"الخطأ": "لا يوجد حملة بهذا الكود"})


def get_BP_instance(id) -> BaseProject:
    try:
        return BaseProject.objects.get(id=id)
    except BaseProject.DoesNotExist:
        raise NotFound({"الخطأ": "لا يوجد مشروع بهذا الكود"})
