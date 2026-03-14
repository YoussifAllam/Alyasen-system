from celery import shared_task
from django.core.mail import EmailMessage
import logging
from apps.Users import models
from config.env import env

# Get an instance of a logger
logger = logging.getLogger("myapp")


@shared_task
def send_email_task(user_id: int, subject: str, message: str) -> None:
    try:
        user = models.User.objects.get(id=user_id)
    except Exception as e:
        logger.error(f"Failed to fetch user: {e}")
    # Send the email
    email = EmailMessage(
        subject=subject,
        body=message,
        to=[user.email],
    )
    email.content_subtype = "html"  # Set the email content type to HTML
    email.send()


@shared_task
def send_email_to_admin(Vendor_user_pk: int) -> None:
    ADMIN_EMAIL1 = env("ADMIN_EMAIL1")
    ADMIN_EMAIL2 = env("ADMIN_EMAIL2")

    try:
        # Fetch the user object
        Vendor_user_obj = models.User.objects.get(id=Vendor_user_pk)
    except Exception as e:
        logger.error(f"Failed to fetch user: {e}")

    subject = "New Vendor request to Be approved"
    message = f"""
        the vendor has requested to be approved.
        name: {Vendor_user_obj.first_name} {Vendor_user_obj.last_name}
        email: {Vendor_user_obj.email}
        and uuid: {Vendor_user_obj.uuid}
        """
    for admin_email in [ADMIN_EMAIL1, ADMIN_EMAIL2]:
        email = EmailMessage(
            subject=subject,
            body=message,
            to=[admin_email],
        )
        email.send()
