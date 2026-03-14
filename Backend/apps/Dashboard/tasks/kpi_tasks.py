from django.db.models import Sum, Count, F
from django.utils import timezone
from cacheops import cached_as
from django.core.cache import cache

from apps.Clients.models import ClientInvoice
from apps.SegmentalSallling.models import Invoice as SegmentalInvoices
from apps.Expenses.models import Expenses
from apps.Material_Warehouse.models import MaterialWarehouse
from apps.Workers.models import WorkersPaidSalary, Workers


class SellingKPIService:
    """Service class for selling-related KPIs using cacheops"""

    @classmethod
    def _fetch_kpi_data_from_db(cls, year, month):
        """
        Fetch KPI data from database for specific year/month
        """
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")

        # Single optimized database query
        client_invoice_result = ClientInvoice.objects.filter(
            invoice_date__year=year, invoice_date__month=month
        ).aggregate(total_amount=Sum("invoice_total_amount"), invoice_count=Count("pk"))

        segmental_invoices_result = SegmentalInvoices.objects.filter(
            invoice_date__year=year, invoice_date__month=month
        ).aggregate(total_amount=Sum("invoice_total_amount"), invoice_count=Count("pk"))

        invoice_count = client_invoice_result["invoice_count"] or 0
        total_amount = client_invoice_result["total_amount"] or 0.0

        invoice_count += segmental_invoices_result["invoice_count"] or 0
        total_amount += segmental_invoices_result["total_amount"] or 0.0

        return {
            "total_amount": float(total_amount),
            "invoice_count": invoice_count,
        }

    @classmethod
    def get_selling_kpi_data(cls, year=None, month=None):
        """
        Get selling KPIs using cacheops automatic caching
        """
        now = timezone.now()
        target_year = year or now.year
        target_month = month or now.month

        # Use cacheops to automatically cache and invalidate
        @cached_as(ClientInvoice, extra=(target_year, target_month))
        def _get_cached_kpi_data():
            return cls._fetch_kpi_data_from_db(target_year, target_month)

        return _get_cached_kpi_data()

    @classmethod
    def get_selling_kpi_data_manual_invalidation(cls, year=None, month=None):
        """
        Alternative: Manual cache control with cacheops
        """
        now = timezone.now()
        target_year = year or now.year
        target_month = month or now.month

        cache_key = f"selling_kpi_{target_year}_{target_month}"

        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data

        # If not in cache, fetch from DB and cache it
        kpi_data = cls._fetch_kpi_data_from_db(target_year, target_month)

        # Cache for 5 minutes
        cache.set(cache_key, kpi_data, 300)

        return kpi_data

    @classmethod
    def invalidate_kpi_cache(cls, year=None, month=None):
        """
        Invalidate cache for specific period using cacheops
        """
        now = timezone.now()
        target_year = year or now.year
        target_month = month or now.month

        # Option 1: Invalidate using cacheops pattern
        from cacheops import invalidate_dict

        invalidate_dict(
            ClientInvoice, {"invoice_date__year": target_year, "invoice_date__month": target_month}
        )

        # Option 2: Invalidate manual cache key
        cache_key = f"selling_kpi_{target_year}_{target_month}"
        cache.delete(cache_key)

        print(f"Cache invalidated for {target_year}-{target_month}")

    @classmethod
    def force_refresh_kpi_data(cls, year=None, month=None):
        """
        Force refresh by invalidating cache first
        """
        cls.invalidate_kpi_cache(year, month)
        return cls.get_selling_kpi_data(year, month)


class ExpensesKPIService:
    """Service class for expenses-related KPIs using cacheops"""

    @classmethod
    def _fetch_kpi_data_from_db(cls, year, month):
        """
        Fetch KPI data from database for specific year/month
        """
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")

        # Single optimized database query for expenses
        result = Expenses.objects.filter(created_date__year=year, created_date__month=month).aggregate(
            total_amount=Sum("amount"),
            transaction_count=Count("pk"),
        )

        transaction_count = result["transaction_count"] or 0
        total_amount = result["total_amount"] or 0.0

        return {
            "total_amount": float(total_amount),
            "transaction_count": transaction_count,
        }

    @classmethod
    def get_expenses_kpi_data(cls, year=None, month=None):
        """
        Get expenses KPIs using cacheops automatic caching
        """
        now = timezone.now()
        target_year = year or now.year
        target_month = month or now.month

        # Use cacheops to automatically cache and invalidate
        @cached_as(Expenses, extra=(target_year, target_month))
        def _get_cached_kpi_data():
            return cls._fetch_kpi_data_from_db(target_year, target_month)

        return _get_cached_kpi_data()

    @classmethod
    def invalidate_kpi_cache(cls, year=None, month=None):
        """
        Invalidate cache for specific period using cacheops
        """
        now = timezone.now()
        target_year = year or now.year
        target_month = month or now.month

        # Option 1: Invalidate using cacheops pattern
        from cacheops import invalidate_dict

        invalidate_dict(Expenses, {"created_date__year": target_year, "created_date__month": target_month})

        # Option 2: Invalidate manual cache keys
        cache_keys = [
            f"expenses_kpi_{target_year}_{target_month}",
            f"expenses_kpi_{target_year}_{target_month}_by_transaction",
            f"expenses_kpi_{target_year}_yearly",
        ]

        for cache_key in cache_keys:
            cache.delete(cache_key)

        print(f"Expenses cache invalidated for {target_year}-{target_month}")

    @classmethod
    def force_refresh_kpi_data(cls, year=None, month=None):
        """
        Force refresh by invalidating cache first
        """
        cls.invalidate_kpi_cache(year, month)
        return cls.get_expenses_kpi_data(year, month)


class MaterialWarehouseKPIService:
    """Service class for Material Warehouse KPIs using cacheops"""

    @classmethod
    def _fetch_kpi_data_from_db(cls):
        """
        Fetch KPI data from database for material warehouse
        """
        # Single optimized database query for material warehouse
        result = MaterialWarehouse.objects.aggregate(
            total_buy_value=Sum(F("quantity_in_unit") * F("buy_price_per_unit")),
            material_count=Count("pk"),
        )

        return {
            "total_buy_value": float(result["total_buy_value"] or 0.0),
            "material_count": result["material_count"] or 0,
        }

    @classmethod
    def get_material_kpi_data(cls):
        """
        Get material warehouse KPIs using cacheops automatic caching
        """

        # Use cacheops to automatically cache and invalidate
        @cached_as(MaterialWarehouse)
        def _get_cached_kpi_data():
            return cls._fetch_kpi_data_from_db()

        return _get_cached_kpi_data()

    @classmethod
    def invalidate_kpi_cache(cls):
        """
        Invalidate cache for material warehouse using cacheops
        """
        # Option 1: Invalidate using cacheops pattern
        from cacheops import invalidate_model

        invalidate_model(MaterialWarehouse)

        # Option 2: Invalidate manual cache keys
        cache_keys = [
            "material_warehouse_kpi",
            "material_warehouse_kpi_profitability",
            "material_warehouse_kpi_low_stock",
            "material_warehouse_kpi_high_value",
            "material_warehouse_kpi_price_summary",
        ]

        for cache_key in cache_keys:
            cache.delete(cache_key)

        print("Material warehouse cache invalidated")

    @classmethod
    def force_refresh_kpi_data(cls):
        """
        Force refresh by invalidating cache first
        """
        cls.invalidate_kpi_cache()
        return cls.get_material_kpi_data()


def get_salary_kpi_data() -> dict:
    total_workers = Workers.objects.count()
    now = timezone.now()
    target_year = now.year
    target_month = now.month

    total_paid_salary = (
        WorkersPaidSalary.objects.filter(
            paid_date__year=target_year, paid_date__month=target_month
        ).aggregate(total_amount=Sum("paid_amount"))["total_amount"]
        or 0
    )
    return total_workers, total_paid_salary


def get_kpi_data() -> dict:
    selling_kpi_data = SellingKPIService.get_selling_kpi_data()
    expenses_kpi_data = ExpensesKPIService.get_expenses_kpi_data()
    material_kpi_data = MaterialWarehouseKPIService.get_material_kpi_data()
    total_workers, total_paid_salary = get_salary_kpi_data()
    salary_kpi_data = {"salary_kpi_data": total_paid_salary, "number_of_employees": total_workers}
    return {
        "selling_kpi_data": selling_kpi_data,
        "expenses_kpi_data": expenses_kpi_data,
        "material_kpi_data": material_kpi_data,
        "salary_kpi_data": salary_kpi_data,
    }
