from rest_framework.request import Request
from cacheops import cached_as
from django.db.models import Q
from rest_framework.exceptions import NotFound

from ..models import CompanyAssets


def get_CompanyAssets_instances(request: Request):
    # Get parameters with proper cleaning
    company_asset_name = request.GET.get("q", "").strip() or None
    print(company_asset_name)
    # Build cache key from non-None parameters
    cache_key = f"company_asset_{company_asset_name}"

    @cached_as(CompanyAssets, extra=cache_key, timeout=3600)
    def _get_cached_query():
        # Build the query
        query = Q()

        if company_asset_name:
            query &= Q(name__icontains=company_asset_name)
            return CompanyAssets.objects.filter(query)

        return CompanyAssets.objects.all()

    return _get_cached_query()


def get_specific_company_asset_instance(company_asset_id: int):
    try:
        return CompanyAssets.objects.get(id=company_asset_id)
    except CompanyAssets.DoesNotExist:
        raise NotFound("Company asset not found")
