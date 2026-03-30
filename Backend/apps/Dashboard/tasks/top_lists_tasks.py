from django.core.cache import cache
from cacheops import cached_as
from django.utils import timezone
from django.db.models import F, Func, Value, Sum
from django.db.models.functions import Abs
from datetime import date

from apps.Quotations.models import Quotations
from apps.Projects.models import BaseProject


class QuotationsReminderService:
    """Service class for client analysis and insights"""

    @classmethod
    def _fetch_pending_quotations_data(cls):
        """
        Fetch quotations data sorted by total balance owed
        """
        reference_date = date.today()
        nearest_quotations = Quotations.objects.filter(
            quotation_last_date__gte=reference_date
        ).order_by("quotation_last_date")[:3]
        return list(nearest_quotations)

    @classmethod
    def get_most_nearest_quotations(cls, limit=3):
        @cached_as(Quotations, extra=("top_3_nearst_quotations", limit))
        def _get_cached_top_3_nearst_quotations():
            quotations_data = cls._fetch_pending_quotations_data()

            if not quotations_data:
                return [
                    {
                        "name": "لا يوجد بيانات",
                        "amount": 0.0,
                        "last_date": "لا يوجد بيانات",
                    },
                    {
                        "name": "لا يوجد بيانات",
                        "amount": 0.0,
                        "last_date": "لا يوجد بيانات",
                    },
                    {
                        "name": "لا يوجد بيانات",
                        "amount": 0.0,
                        "last_date": "لا يوجد بيانات",
                    },
                ]

            top_3_nearst_quotations = []
            for quotation in quotations_data[:limit]:

                top_3_nearst_quotations.append(
                    {
                        "name": quotation.company_name,
                        "amount": quotation.price,
                        "last_date": quotation.quotation_last_date,
                    }
                )

            return top_3_nearst_quotations

        return _get_cached_top_3_nearst_quotations()

    @classmethod
    def invalidate_cache(cls):
        """
        Invalidate client analysis cache
        """
        from cacheops import invalidate_model

        invalidate_model(Quotations)

        cache_keys = [
            "top_3_nearst_quotations",
        ]

        for cache_key in cache_keys:
            cache.delete(cache_key)

        print("Quotations cache invalidated")

    @classmethod
    def force_refresh_analysis(cls):
        """
        Force refresh analysis data
        """
        cls.invalidate_cache()
        return cls.get_top_clients_by_balance(3)


class ProjectsReminderService:
    """Service class for projects analysis and insights"""

    @classmethod
    def _fetch_top_active_projects_data(cls):
        """
        Fetch active projects data sorted by highest cost
        """
        top_projects = BaseProject.objects.filter(project_status="active").order_by(
            "-cost"
        )[:3]
        return list(top_projects)

    @classmethod
    def get_top_active_projects(cls, limit=3):
        @cached_as(BaseProject, extra=("top_3_active_projects", limit))
        def _get_cached_top_active_projects():
            projects_data = cls._fetch_top_active_projects_data()

            if not projects_data:
                return [
                    {
                        "name": "لا يوجد بيانات",
                        "cost": 0.0,
                        "supplier": "لا يوجد بيانات",
                    },
                    {
                        "name": "لا يوجد بيانات",
                        "cost": 0.0,
                        "supplier": "لا يوجد بيانات",
                    },
                    {
                        "name": "لا يوجد بيانات",
                        "cost": 0.0,
                        "supplier": "لا يوجد بيانات",
                    },
                ]

            top_active_projects = []
            for project in projects_data[:limit]:
                top_active_projects.append(
                    {
                        "name": project.name,
                        "cost": project.cost,
                        "supplier": (
                            project.supplier.name
                            if project.supplier
                            else "لا يوجد مورد"
                        ),
                    }
                )

            return top_active_projects

        return _get_cached_top_active_projects()

    @classmethod
    def invalidate_cache(cls):
        """
        Invalidate projects analysis cache
        """
        from cacheops import invalidate_model

        invalidate_model(BaseProject)

        cache_keys = [
            "top_3_active_projects",
        ]

        for cache_key in cache_keys:
            cache.delete(cache_key)

        print("Projects cache invalidated")

    @classmethod
    def force_refresh_analysis(cls):
        """
        Force refresh analysis data
        """
        cls.invalidate_cache()
        return cls.get_top_active_projects(3)


def get_top_data():
    """
    This function aggregates the data from different services into the final
    dictionary that will be nested under the 'data' key in the API response.
    """
    top_3_nearst_quotations = QuotationsReminderService.get_most_nearest_quotations()
    projects = ProjectsReminderService.get_top_active_projects()

    return {
        "top_3_nearst_quotations": top_3_nearst_quotations,
        "top_active_projects": projects,
    }
