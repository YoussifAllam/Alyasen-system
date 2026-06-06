from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_date

from ..models import Safe, SafeLogs


def get_safe_balance():
    safe_instance, _created = Safe.objects.get_or_create(id=1)
    return safe_instance.balance


def get_safe_logs(
    *,
    date=None,
    date_from=None,
    date_to=None,
    operation_type=None,
    search=None,
):
    queryset = SafeLogs.objects.all()

    if date:
        parsed = parse_date(date) if isinstance(date, str) else date
        if parsed:
            queryset = queryset.filter(date__date=parsed)

    if date_from:
        parsed_from = parse_date(date_from) if isinstance(date_from, str) else date_from
        if parsed_from:
            queryset = queryset.filter(date__date__gte=parsed_from)

    if date_to:
        parsed_to = parse_date(date_to) if isinstance(date_to, str) else date_to
        if parsed_to:
            queryset = queryset.filter(date__date__lte=parsed_to)

    if operation_type:
        queryset = queryset.filter(operation_type=operation_type)

    if search:
        queryset = queryset.filter(trnasaction__icontains=search.strip())

    return queryset


def get_safe_summary():
    balance = get_safe_balance()
    now = timezone.now()
    if timezone.is_naive(now):
        now = timezone.make_aware(now)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    last_log = SafeLogs.objects.order_by("-date").first()
    last_updated = last_log.date.isoformat() if last_log else None

    yesterday_last = (
        SafeLogs.objects.filter(date__lt=today_start)
        .exclude(balance_after__isnull=True)
        .order_by("-date")
        .first()
    )
    yesterday_balance = yesterday_last.balance_after if yesterday_last else None
    change_vs_yesterday = (
        balance - yesterday_balance if yesterday_balance is not None else None
    )

    today_qs = SafeLogs.objects.filter(date__gte=today_start)
    today_deposits = (
        today_qs.filter(operation_type="deposit").aggregate(total=Sum("amount"))["total"]
        or 0.0
    )
    today_withdrawals = (
        today_qs.filter(operation_type="withdrawal").aggregate(total=Sum("amount"))[
            "total"
        ]
        or 0.0
    )

    return {
        "balance": balance,
        "currency": "جنيه",
        "last_updated": last_updated,
        "yesterday_balance": yesterday_balance,
        "change_vs_yesterday": change_vs_yesterday,
        "today_deposits": today_deposits,
        "today_withdrawals": today_withdrawals,
    }
