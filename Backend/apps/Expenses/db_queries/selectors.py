from rest_framework.request import Request
from cacheops import cached_as
from django.db.models import Sum, Q
from django.utils.timezone import localdate
from ..models import Expenses


def get_expenses_instances(request: Request):
    # Get parameters with proper cleaning
    transaction = request.GET.get("transaction", "").strip() or None
    created_date = request.GET.get("created_date", "").strip() or None
    permit_number = request.GET.get("permit_number", "").strip() or None

    # Build cache key from non-None parameters
    cache_key = f"transactions_{transaction}_{created_date}_{permit_number}"

    @cached_as(Expenses, extra=cache_key, timeout=3600)
    def _get_cached_query():
        # Build the query
        query = Q()

        if transaction:
            query &= Q(transaction=transaction)
        if created_date:
            query &= Q(created_date=created_date)
        if permit_number:
            query &= Q(permit_number=permit_number)

        # Return the queryset itself (cacheops will handle it)
        return Expenses.objects.filter(query)

    return _get_cached_query()


def get_expenses_stats():
    """
    Get comprehensive expenses statistics including:
    - Total amount of expenses for today
    - Total amount of expenses for current month
    - Total number of expenses for today
    """
    today = localdate()
    print(today)
    month_start = today.replace(day=1)

    # Today's expenses
    today_expenses = Expenses.objects.filter(created_date=today)

    # Current month expenses
    month_expenses = Expenses.objects.filter(
        created_date__year=month_start.year, created_date__month=month_start.month
    )

    # Calculate statistics
    stats = {
        "today_total_amount": today_expenses.aggregate(total=Sum("amount"))["total"] or 0.0,
        "month_total_amount": month_expenses.aggregate(total=Sum("amount"))["total"] or 0.0,
        "month_count": month_expenses.count(),
    }

    return stats
