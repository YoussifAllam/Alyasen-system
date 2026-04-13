from celery import shared_task
from django.utils.timezone import localdate
from datetime import timedelta
from ..models import industrial_projects_models, rent_projects_models
from apps.Notifications.views import send_notification_function


@shared_task(name="check_insurance_tax_deadline")
def check_insurance_tax_deadline():
    today = localdate()
    two_days_later = today + timedelta(days=2)

    # Check Selling Industrial Projects
    ind_projects = (
        industrial_projects_models.SellingIndustrialProjectDetails.objects.filter(
            insurance_tax_date__lte=two_days_later,
            insurance_tax_date__gte=today,
            insurance_tax_cleared=False,
        )
    )

    for project in ind_projects:
        title = f"تنبيه: استرداد تأمين مشروع {project.CPB_fk.project_name}"
        message = (
            f"تاريخ استرداد التأمين للمشروع (رقم {project.CPB_fk.id}) هو {project.insurance_tax_date}. "
            "يرجى اتخاذ الإجراءات اللازمة."
        )
        send_notification_function(title, message)

    # Check Rent Projects
    rent_projects = rent_projects_models.RentProjects.objects.filter(
        insurance_tax_date__lte=two_days_later,
        insurance_tax_date__gte=today,
        insurance_tax_cleared=False,
    )

    for project in rent_projects:
        title = f"تنبيه: استرداد تأمين مشروع {project.CPB_fk.project_name}"
        message = (
            f"تاريخ استرداد التأمين للمشروع (رقم {project.CPB_fk.id}) هو {project.insurance_tax_date}. "
            "يرجى اتخاذ الإجراءات اللازمة."
        )
        send_notification_function(title, message)
