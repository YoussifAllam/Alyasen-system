import os
import logging
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND


from ..db_queries import selectors
from ..models import Client, ClientProjectBalance
from ..serializers import OutputSerializers

logger = logging.getLogger("debug")


def send_financial_report_email(client_id: int):
    if not client_id:
        logger.warning("send_financial_report_email called without client_id")
        return {"error": "client_id is required"}, HTTP_400_BAD_REQUEST

    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        logger.warning(
            "Client not found while sending report email: client_id=%s", client_id
        )
        return {"error": "Client not found"}, HTTP_404_NOT_FOUND

    if not client.email:
        logger.warning("Client has no email address: client_id=%s", client_id)
        return {"error": "Client has no email address"}, HTTP_400_BAD_REQUEST

    # Fetch projects and campaigns
    projects, campaigns = selectors.get_client_project_and_campaings(client_id)
    projects_serializer = OutputSerializers.BaseProjectSerializer(projects, many=True)
    campaigns_serializer = OutputSerializers.CampaineSerializer(campaigns, many=True)

    projects_list = [dict(item) for item in projects_serializer.data]
    campaigns_list = [dict(item) for item in campaigns_serializer.data]

    all_items = projects_list + campaigns_list

    # Compute totals / normalize
    for item in all_items:
        item["normalized_cost"] = item.get("total_cost", item.get("cost", 0))

    context = {
        "client": client,
        "items": all_items,
        "total_cost": client.total_balance_owed_to_us,
        "total_paid": client.total_paid_amount,
        "total_remaining": client.total_remaining_balance_owed_to_us,
    }

    logger.info(
        "Preparing financial report email for client_id=%s email=%s items=%s",
        client_id,
        client.email,
        len(all_items),
    )

    try:
        html_content = render_to_string("financial_report.html", context)
    except Exception:
        logger.exception(
            "Failed to render financial report template for client_id=%s", client_id
        )
        return {"error": "Failed to render email template"}, HTTP_400_BAD_REQUEST

    email = EmailMessage(
        subject=f"التقرير المالي - {client.name}",
        body=html_content,
        to=[client.email],
    )
    email.content_subtype = "html"

    logo_path = os.path.join(settings.BASE_DIR, "static", "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", "<logo>")
            img.add_header("Content-Disposition", "inline", filename="logo.png")
            email.attach(img)
    else:
        logger.warning("Logo not found for email attachment: %s", logo_path)

    try:
        sent_count = email.send(fail_silently=False)
        logger.info(
            "Financial report email send result client_id=%s sent_count=%s",
            client_id,
            sent_count,
        )
        if sent_count != 1:
            return {
                "error": "Email was not accepted by SMTP server"
            }, HTTP_400_BAD_REQUEST
    except Exception as exc:
        logger.exception(
            "Failed sending financial report email for client_id=%s recipient=%s",
            client_id,
            client.email,
        )
        return {"error": f"Email sending failed: {str(exc)}"}, HTTP_400_BAD_REQUEST

    return {"message": "Financial report sent successfully"}, HTTP_200_OK
