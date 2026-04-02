from .. import models
from rest_framework.request import Request
from cacheops import cached_as


# def get_transactions(request: Request):
#     username = request.GET.get("username")
#     created_date = request.GET.get("created_date")

#     # Create a cache key based on the query parameters
#     cache_key = f"transactions_{username}_{created_date}"

#     # Use cached_as to cache the queryset
#     @cached_as(models.TransactionsLog, extra=cache_key, timeout=3600)
#     def _get_filtered_transactions():

#         if username and not created_date:
#             return models.TransactionsLog.objects.filter(username=username)

#         if created_date and not username:
#             return models.TransactionsLog.objects.filter(created_date=created_date)

#         if username and created_date:
#             return models.TransactionsLog.objects.filter(username=username, created_date=created_date)

#         return models.TransactionsLog.objects.all()

#     result = _get_filtered_transactions()
#     return result
