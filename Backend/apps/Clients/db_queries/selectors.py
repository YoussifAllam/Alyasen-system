from rest_framework.request import Request
from cacheops import cached_as
from django.db.models import Q
from rest_framework.exceptions import NotFound

from ..models import Client

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


# def get_client_payments_instances(client_id: int):
#     return InvoicePayment.objects.filter(client_fk__id=client_id)


def get_client_project_and_campaings(client_id):
    projects = BaseProject.objects.filter(client=client_id)
    campaigns = Campaine.objects.filter(client=client_id)
    return projects, campaigns
