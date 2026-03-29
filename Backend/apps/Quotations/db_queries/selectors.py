from .. import models
from rest_framework.request import Request
from cacheops import cached_as
from rest_framework.exceptions import NotFound


def get_quotations(request: Request):
    client_name = request.GET.get("client_name")

    # Create a cache key based on the query parameters
    cache_key = f"quotations_{client_name}"

    # Use cached_as to cache the queryset
    @cached_as(models.Quotations, extra=cache_key, timeout=3600)
    def _get_filtered_quotations():

        if client_name:
            return models.Quotations.objects.filter(client_name=client_name)

        return models.Quotations.objects.all()

    result = _get_filtered_quotations()
    return result


def get_specific_quotation(id: int):
    try:
        return models.Quotations.objects.get(id=id)
    except models.Quotations.DoesNotExist:
        raise NotFound({"الخطأ": "لا يوجد عرض سعر بهذا الكود"})


def get_quotation_attachments(q_id):
    try:
        return models.QuotationsAttachments.objects.filter(quotation_id=q_id)
    except models.QuotationsAttachments.DoesNotExist:
        raise NotFound({"الخطأ": "لا يوجد مرفقات لهذا العرض"})
