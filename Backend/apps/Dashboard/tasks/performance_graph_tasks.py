from django.db.models import Sum
from django.utils import timezone
from django.core.cache import cache
from cacheops import cached_as

from apps.Clients.models import ClientInvoice
from apps.Expenses.models import Expenses


class PerformanceAnalysisService:
    """Service class for performance analysis (sales vs expenses)"""

    @classmethod
    def _get_arabic_month_names(cls):
        """Return Arabic month names"""
        return {
            1: "يناير",
            2: "فبراير",
            3: "مارس",
            4: "أبريل",
            5: "مايو",
            6: "يونيو",
            7: "يوليو",
            8: "أغسطس",
            9: "سبتمبر",
            10: "أكتوبر",
            11: "نوفمبر",
            12: "ديسمبر",
        }

    @classmethod
    def _fetch_sales_data_by_month(cls, year):
        """
        Fetch sales data grouped by month for the given year
        """
        sales_data = (
            ClientInvoice.objects.filter(invoice_date__year=year)
            .values("invoice_date__month")
            .annotate(total_sales=Sum("invoice_total_amount"))
            .order_by("invoice_date__month")
        )

        return {item["invoice_date__month"]: float(item["total_sales"] or 0) for item in sales_data}

    @classmethod
    def _fetch_expenses_data_by_month(cls, year):
        """
        Fetch expenses data grouped by month for the given year
        """
        expenses_data = (
            Expenses.objects.filter(created_date__year=year)
            .values("created_date__month")
            .annotate(total_expenses=Sum("amount"))
            .order_by("created_date__month")
        )

        return {item["created_date__month"]: float(item["total_expenses"] or 0) for item in expenses_data}

    @classmethod
    def get_performance_data(cls, year=None):
        """
        Get performance data (sales vs expenses) for the given year
        """
        if year is None:
            year = timezone.now().year

        @cached_as(ClientInvoice, Expenses, extra=("performance_data", year))
        def _get_cached_performance_data():
            # Fetch data from both models
            sales_by_month = cls._fetch_sales_data_by_month(year)
            expenses_by_month = cls._fetch_expenses_data_by_month(year)

            arabic_months = cls._get_arabic_month_names()

            # Prepare data for all months
            labels = []
            sales = []
            expenses = []

            for month in range(1, 13):
                labels.append(arabic_months[month])
                sales.append(sales_by_month.get(month, 0.0))
                expenses.append(expenses_by_month.get(month, 0.0))

            return {
                "status": "success",
                "data": {"year": year, "labels": labels, "sales": sales, "expenses": expenses},
            }

        return _get_cached_performance_data()

    @classmethod
    def get_current_year_performance(cls):
        """
        Get performance data for current year only
        """
        current_year = timezone.now().year
        return cls.get_performance_data(current_year)

    @classmethod
    def invalidate_performance_cache(cls, year=None):
        """
        Invalidate performance analysis cache
        """
        from cacheops import invalidate_dict

        if year:
            # Invalidate for specific year
            invalidate_dict(ClientInvoice, {"invoice_date__year": year})
            invalidate_dict(Expenses, {"created_date__year": year})

            cache_keys = [
                f"performance_data_{year}",
                f"performance_with_profit_{year}",
            ]
        else:
            # Invalidate all years
            invalidate_dict(ClientInvoice)
            invalidate_dict(Expenses)

            # Get all available years and invalidate their caches
            years = cls.get_available_years()
            cache_keys = []
            for year in years:
                cache_keys.extend(
                    [
                        f"performance_data_{year}",
                        f"performance_with_profit_{year}",
                    ]
                )

        for cache_key in cache_keys:
            cache.delete(cache_key)

        print(f"Performance analysis cache invalidated for year: {year or 'all'}")

    @classmethod
    def force_refresh_performance_data(cls, year=None):
        """
        Force refresh performance data
        """
        cls.invalidate_performance_cache(year)
        return cls.get_performance_data(year)
