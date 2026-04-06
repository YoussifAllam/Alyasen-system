from celery import shared_task
from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Q
from ..models import ProjectPayment
from apps.Notifications.views import (
    send_notification_function,
)  # Import your notification function


@shared_task
def check_check_cleared_notifications():
    """
    Celery task to check for check payments that are clearing today or within 2 days.
    Runs daily at 12:00 AM.
    """
    today = date.today()
    target_date = today + timedelta(days=2)

    # Find payments that meet the criteria:
    # 1. check_cleared_date is today
    # 2. check_cleared_date is within 2 days from today
    # 3. payment_type is 'check' (assuming you have 'check' in PaymentTypes)
    # 4. Exclude already notified payments if you have a flag (optional)

    payments_to_notify = ProjectPayment.objects.filter(
        Q(check_cleared_date=today) | Q(check_cleared_date=target_date),
        payment_type="check",  # Only check payments
        check_cleared_date__isnull=False,
    ).select_related("client_project_balance_fk__client_fk")

    notifications_sent = 0

    for payment in payments_to_notify:
        # Determine notification type based on date
        if payment.check_cleared_date == today:
            title = "تنبيه: موعد صرف الشيك اليوم"
            message = (
                f"العميل/{payment.client_project_balance_fk.client_fk.name}\n"
                f"يوجد شيك قيمته {payment.payment_amount} جنيه سيتم صرفه اليوم {payment.check_cleared_date}\n"
                f"رقم فاتورة البوابة: {payment.portal_invoice_number}\n"
            )
        elif payment.check_cleared_date == target_date:
            title = "تنبيه: موعد صرف الشيك بعد يومين"
            message = (
                f"العميل/{payment.client_project_balance_fk.client_fk.name}\n"
                f"يوجد شيك قيمته {payment.payment_amount} جنيه سيتم صرفه بتاريخ {payment.check_cleared_date}\n"
                f"رقم فاتورة البوابة: {payment.portal_invoice_number}\n"
            )
        else:
            # For dates that are exactly 2 days from today
            days_until = (payment.check_cleared_date - today).days
            if 1 <= days_until <= 2:
                title = f"تنبيه: موعد صرف الشيك بعد {days_until} يوم"
                message = (
                    f"العميل/{payment.client_project_balance_fk.client_fk.name}\n"
                    f"يوجد شيك قيمته {payment.payment_amount} جنيه سيتم صرفه بعد {days_until} يوم بتاريخ {payment.check_cleared_date}\n"  # noqa
                    f"رقم فاتورة البوابة: {payment.portal_invoice_number}\n"
                )
            else:
                continue

        # Send notification
        send_notification_function(title, message)
        notifications_sent += 1

        # Optional: Log or mark as notified if you have a field for that
        # payment.notification_sent = True
        # payment.save()

    return f"Sent {notifications_sent} notifications for check clearing dates"
