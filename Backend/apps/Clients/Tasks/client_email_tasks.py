# emails.py (or in your views.py / services.py)

import io
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
import os
from email.mime.image import MIMEImage
from django.conf import settings


from ..db_queries import selectors
from ..serializers import OutputSerializers
from ..models import Client, ClientProjectBalance


def send_financial_report_email(client_id: int):
    if not client_id:
        return {"error": "client_id is required"}, HTTP_400_BAD_REQUEST

    try:
        client = Client.objects.get(id=client_id)
    except Client.DoesNotExist:
        return {"error": "Client not found"}, HTTP_404_NOT_FOUND

    if not client.email:
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

    logo_path = os.path.join(settings.BASE_DIR, "static", "logo.png")  # adjust path

    context = {
        "client": client,
        "items": all_items,
        "total_cost": client.total_balance_owed_to_us,
        "total_paid": client.total_paid_amount,
        "total_remaining": client.total_remaining_balance_owed_to_us,
    }
    print("\n context", context)

    html_content = render_to_string("financial_report.html", context)

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
    email.send()

    return {"message": "Financial report sent successfully"}, HTTP_200_OK
