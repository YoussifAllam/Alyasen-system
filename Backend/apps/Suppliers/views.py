from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from django.db import transaction

from .tasks.Pagenator import pagenator
from .db_queries import selectors, services
from .serializers import InputSerializers, OutputSerializers, ParamsSerializers
from .tasks import celery_tasks

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import Supplier, SupplierProjectBalance  # adjust import path
import os
from django.templatetags.static import static
from email.mime.image import MIMEImage


class SupplierApiView(APIView):
    def get(self, request: Request, format=None):
        filtred_transactions = selectors.get_suppliers(request)

        response_data = pagenator(
            filtred_transactions, request, OutputSerializers.SupplierSerializer
        )

        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        serializer = InputSerializers.SupplierSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "faild", "errors": serializer.errors}, status=400
            )
        serializer.save()

        tranaction = "تم أضافة مورد جديد للنظام"
        username = request.data["username"]
        create_transaction_log(transaction_data=tranaction, username=username)

        return Response({"status": "success"}, status=HTTP_200_OK)


class SupplierInfoApiView(APIView):
    def get(self, request: Request, format=None):
        supplier_id = request.GET.get("id")
        print("supplier_id", supplier_id)
        supplier_instance = selectors.get_supplier_instance(supplier_id)
        serializer = OutputSerializers.SupplierSerializer(
            supplier_instance, many=False, context={"request": request}
        )
        return Response({"status": "succes", "data": serializer.data}, 200)


class SupplierProjectsApiView(APIView):
    def get(self, request: Request, format=None):
        supplier_id = request.GET.get("supplier_id")
        supplier_projects = selectors.get_supplier_projects(supplier_id)
        response_data = pagenator(
            supplier_projects,
            request,
            OutputSerializers.SupplierProjectsSerializer,
            page_size=10,
        )
        return Response(response_data, 200)


class InovicePaymentApiView(APIView):
    def post(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(
            ParamsSerializers.InvoicePaymentSerializer, data=request.data
        )
        supplier_id = request.data["supplier_id"]
        project_id = request.data["project_id"]
        payment_amount = float(request.data["payment_amount"])

        supplier_instance = selectors.get_supplier_instance(supplier_id)
        project_instance = selectors.get_project_balance_instance(project_id)

        if (
            payment_amount > supplier_instance.total_amount_payable
            or payment_amount > project_instance.remining  # noqa
        ):
            return Response({"error": "المبلغ المدفوع اكبر من المتبقي "}, 400)

        services.pay_for_supplier(supplier_instance, payment_amount)
        services.pay_for_project(project_instance, payment_amount)

        serializer = InputSerializers.InvoicePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "faild", "errors": serializer.errors}, status=400
            )
        serializer.save(
            supplier_fk=supplier_instance, project_fk=project_instance.project_fk
        )

        create_transaction_log.delay(
            username=request.data["username"],
            transaction_data=f"تم تسديد دفعه للمورد {supplier_instance.name} بمبلغ {payment_amount}",
        )

        return Response({"status": "sucess"}, 200)

    def get(Self, request: Request, format=None):
        supplier_id = request.GET.get("supplier_id")
        project_balance_id = request.GET.get("project_id")
        payments_instances = selectors.get_supplier_payments_instances(
            supplier_id, project_balance_id
        )

        response_data = pagenator(
            payments_instances, request, OutputSerializers.InvoicePaymentsSerializer
        )
        return Response(response_data, 200)


def send_supplier_report(request, supplier_id):
    supplier = get_object_or_404(Supplier, pk=supplier_id)

    # 1. Validate email
    if not supplier.email:
        return HttpResponse(
            f"Supplier '{supplier.name}' has no email address.", status=400
        )

    # 2. Gather project balances
    project_balances = SupplierProjectBalance.objects.filter(
        supplier_fk=supplier
    ).select_related("project_fk")

    # 3. Prepare context for the HTML template
    logo_path = os.path.join(settings.BASE_DIR, "static", "logo.png")  # adjust path

    context = {
        "supplier": supplier,
        "project_balances": project_balances,
    }

    print("_-----------", request.build_absolute_uri(settings.STATIC_URL + "logo.png"))

    # 4. Render HTML email content
    html_content = render_to_string("report_email.html", context)
    text_content = strip_tags(html_content)  # plain text fallback

    # 5. Build and send email
    subject = f"Supplier Report – {supplier.name}"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [supplier.email]

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    msg.attach_alternative(html_content, "text/html")
    msg.mixed_subtype = "related"  # important!

    # Attach logo with a Content-ID
    logo_path = os.path.join(settings.BASE_DIR, "static", "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", "<logo>")
            img.add_header("Content-Disposition", "inline", filename="logo.png")
            msg.attach(img)

    msg.send()

    return HttpResponse(f"Report sent successfully to {supplier.email}")
