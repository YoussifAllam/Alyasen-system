from celery import shared_task
from django.core.mail import EmailMessage, get_connection

from apps.Users.models import User

import logging

logger = logging.getLogger("debug")


@shared_task
def send_email_to_all_users_task(subject: str, message: str) -> None:
    """Send email to all users with bulk operation."""
    try:
        # Get all users
        users = User.objects.filter(is_active=True)

        # Create email messages
        emails = []
        for user in users:
            email = EmailMessage(
                subject=subject,
                body=message,
                to=[user.email],
            )
            email.content_subtype = "html"
            emails.append(email)

        # Send all emails
        connection = get_connection()
        connection.send_messages(emails)

        logger.info(f"Successfully sent emails to {len(users)} users")

    except Exception as e:
        logger.error(f"Failed to send bulk emails: {e}")
        raise
