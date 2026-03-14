from django.db.models import Sum
from django.utils import timezone
from django.core.cache import cache
from cacheops import cached_as
from apps.Expenses.models import Expenses


class ExpensesAnalysisService:
    """Service class for expenses analysis and breakdown"""

    @classmethod
    def _fetch_current_month_expenses(cls):
        """
        Fetch current month expenses data from database
        """
        now = timezone.now()
        current_year = now.year
        current_month = now.month

        # Get all transactions for current month grouped by transaction type
        print(f"Fetching expenses for {current_year}-{current_month}")
        expenses_data = (
            Expenses.objects.filter(created_date__year=current_year, created_date__month=current_month)
            .values("transaction")
            .annotate(total_amount=Sum("amount"))
            .order_by("-total_amount")
        )

        return list(expenses_data), current_year, current_month

    @classmethod
    def get_expenses_breakdown(cls):
        """
        Get expenses breakdown with top 2 transactions and others summarized
        Returns: {
            'top_expenses': [
                {'name': 'Salary', 'amount': 70000, 'percentage': 70.0},
                {'name': 'Material', 'amount': 20000, 'percentage': 20.0}
            ],
            'others': {'name': 'Others', 'amount': 10000, 'percentage': 10.0},
            'total_amount': 100000,
            'period': '2024-01'
        }
        """
        now = timezone.now()
        current_year = now.year
        current_month = now.month

        @cached_as(Expenses, extra=(current_year, current_month, "breakdown"))
        def _get_cached_breakdown():
            expenses_data, year, month = cls._fetch_current_month_expenses()

            if not expenses_data:
                return {
                    "top_expenses": [],
                    "others": {"name": "Others", "amount": 0, "percentage": 0.0},
                    "total_amount": 0,
                }

            # Calculate total amount
            total_amount = sum(item["total_amount"] for item in expenses_data)

            # Get top 2 expenses
            top_expenses = []
            for item in expenses_data[:2]:
                percentage = (item["total_amount"] / total_amount) * 100 if total_amount > 0 else 0
                top_expenses.append(
                    {
                        "name": item["transaction"],
                        "amount": float(item["total_amount"]),
                        "percentage": round(percentage, 2),
                    }
                )

            # Calculate others (remaining expenses beyond top 2)
            others_amount = sum(item["total_amount"] for item in expenses_data[2:])
            others_percentage = (others_amount / total_amount) * 100 if total_amount > 0 else 0

            others_data = {
                "name": "Others",
                "amount": float(others_amount),
                "percentage": round(others_percentage, 2),
            }

            return {
                "top_expenses": top_expenses,
                "others": others_data,
                "total_amount": float(total_amount),
            }

        return _get_cached_breakdown()

    @classmethod
    def invalidate_cache(cls):
        """
        Invalidate expenses analysis cache
        """
        now = timezone.now()
        current_year = now.year
        current_month = now.month

        from cacheops import invalidate_dict

        invalidate_dict(Expenses, {"created_date__year": current_year, "created_date__month": current_month})

        cache_keys = [
            f"expenses_breakdown_{current_year}_{current_month}",
            f"expenses_detailed_breakdown_{current_year}_{current_month}",
            f"expenses_chart_data_{current_year}_{current_month}",
        ]

        for cache_key in cache_keys:
            cache.delete(cache_key)

        print(f"Expenses analysis cache invalidated for {current_year}-{current_month}")

    @classmethod
    def force_refresh_analysis(cls):
        """
        Force refresh analysis data
        """
        cls.invalidate_cache()
        return cls.get_expenses_breakdown()
