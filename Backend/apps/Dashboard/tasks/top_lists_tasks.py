from django.core.cache import cache
from cacheops import cached_as
from django.utils import timezone
from django.db.models import Sum

from apps.Clients.models import Client, InvoiceMaterials, ClientInvoice


class ClientAnalysisService:
    """Service class for client analysis and insights"""

    @classmethod
    def _fetch_clients_balance_data(cls):
        """
        Fetch clients data sorted by total balance owed
        """
        clients_data = Client.objects.only("name", "total_balance_owed_to_us").order_by(
            "-total_balance_owed_to_us"
        )
        return list(clients_data)

    @classmethod
    def get_top_clients_by_balance(cls, limit=3):
        # @cached_as(Client, extra=("top_balance", limit))
        def _get_cached_top_clients():
            clients_data = cls._fetch_clients_balance_data()

            if not clients_data:
                return [
                    {"name": "لا يوجد بيانات", "amount": 0.0},
                    {"name": "لا يوجد بيانات", "amount": 0.0},
                    {"name": "لا يوجد بيانات", "amount": 0.0},
                ]

            top_clients = []
            for client in clients_data[:limit]:

                top_clients.append(
                    {
                        "name": client.name,
                        "amount": float(client.total_balance_owed_to_us),
                    }
                )

            return top_clients

        return _get_cached_top_clients()

    @classmethod
    def invalidate_cache(cls):
        """
        Invalidate client analysis cache
        """
        from cacheops import invalidate_model

        invalidate_model(Client)

        cache_keys = [
            "clients_top_balance",
            "clients_top_balance_with_others",
            "clients_balance_stats",
            "clients_overdue_insights",
        ]

        for cache_key in cache_keys:
            cache.delete(cache_key)

        print("Client analysis cache invalidated")

    @classmethod
    def force_refresh_analysis(cls):
        """
        Force refresh analysis data
        """
        cls.invalidate_cache()
        return cls.get_top_clients_by_balance(3)


class MixtureAnalysisService:
    """Service class for mixture analysis from invoices"""

    @classmethod
    def _fetch_current_month_mixtures_data(cls):
        """
        Fetch mixtures data from current month invoices
        """
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        mixtures_data = (
            InvoiceMaterials.objects.only("invoice__invoice_date", "material__material_name", "quantity_in_unit") # todo: change to material
            .filter(invoice__invoice_date__year=current_year, invoice__invoice_date__month=current_month)
            .values("material__material_name", "material_id")
            .annotate(
                total_quantity=Sum("quantity_in_unit"),
            )
            .order_by("-total_quantity")
        )
        return list(mixtures_data)

    @classmethod
    def get_top_mixtures_current_month(cls, limit=3):
        now = timezone.now()
        current_year = now.year
        current_month = now.month

        # @cached_as(InvoiceMaterials, ClientInvoice, extra=(current_year, current_month, "top_mixtures", limit))
        def _get_cached_top_mixtures():
            mixtures_data = cls._fetch_current_month_mixtures_data()

            # todo: change this
            # if not mixtures_data: 
            return [
                    {"name": "لا يوجد بيانات", "total_quantity": 0.0},
                    {"name": "لا يوجد بيانات", "total_quantity": 0.0},
                    {"name": "لا يوجد بيانات", "total_quantity": 0.0},
                ]

            # top_mixtures = []
            # for item in mixtures_data[:limit]:
            #     top_mixtures.append(
            #         {"name": item["mixture__name"], "total_quantity": float(item["total_quantity"])}
            #     )

            # return top_mixtures

        return _get_cached_top_mixtures()

    @classmethod
    def invalidate_cache(cls):
        """
        Invalidate mixture analysis cache
        """
        now = timezone.now()
        current_year = now.year
        current_month = now.month

        from cacheops import invalidate_dict

        # Invalidate for both models
        invalidate_dict(
            InvoiceMaterials,
            {"invoice__invoice_date__year": current_year, "invoice__invoice_date__month": current_month},
        )
        invalidate_dict(
            ClientInvoice, {"invoice_date__year": current_year, "invoice_date__month": current_month}
        )

        cache_keys = [
            f"mixtures_top_{current_year}_{current_month}",
            f"mixtures_top_with_others_{current_year}_{current_month}",
            f"mixtures_monthly_stats_{current_year}_{current_month}",
            f"mixtures_profitable_{current_year}_{current_month}",
        ]

        for cache_key in cache_keys:
            cache.delete(cache_key)

        print(f"Mixture analysis cache invalidated for {current_year}-{current_month}")

    @classmethod
    def force_refresh_analysis(cls):
        """
        Force refresh analysis data
        """
        cls.invalidate_cache()
        return cls.get_top_mixtures_current_month(3)


def get_top_data():
    """
    This function aggregates the data from different services into the final
    dictionary that will be nested under the 'data' key in the API response.
    """
    top_client_list = ClientAnalysisService.get_top_clients_by_balance()
    top_materials_list = MixtureAnalysisService.get_top_mixtures_current_month()

    return {"top_client_list": top_client_list, "top_materials_list": top_materials_list}
