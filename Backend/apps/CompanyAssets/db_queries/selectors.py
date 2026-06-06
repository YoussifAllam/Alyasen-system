from django.db.models import Count, Q, Sum
from rest_framework.exceptions import NotFound
from rest_framework.request import Request

from ..models import CompanyAssets, CompanyAssetsAttachments


def get_CompanyAssets_instances(request: Request):
    queryset = CompanyAssets.objects.all()

    search = request.GET.get("q", "").strip()
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(location__icontains=search)
            | Q(responsible_person__icontains=search)
            | Q(details__icontains=search)
        )

    category = request.GET.get("category", "").strip()
    if category:
        queryset = queryset.filter(category=category)

    status = request.GET.get("status", "").strip()
    if status:
        queryset = queryset.filter(status=status)

    return queryset.order_by("-id")


def get_company_assets_summary(queryset):
    aggregated = queryset.aggregate(
        count=Count("id"),
        total_value=Sum("price"),
    )
    return {
        "count": aggregated["count"] or 0,
        "total_value": float(aggregated["total_value"] or 0),
    }


def get_specific_company_asset_instance(company_asset_id: int):
    try:
        return CompanyAssets.objects.get(id=company_asset_id)
    except CompanyAssets.DoesNotExist:
        raise NotFound("Company asset not found")


def get_CompanyAssetsAttachments_instances(asset_id: int):
    return CompanyAssetsAttachments.objects.filter(asset_id=asset_id)
