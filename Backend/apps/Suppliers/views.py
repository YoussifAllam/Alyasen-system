from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from django.db import transaction

from .tasks.pagenator import pagenator
from .db_queries import selectors, services
from .serializers import InputSerializers, OutputSerializers, ParamsSerializers
from .tasks import celery_tasks

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


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
        serializer = OutputSerializers.SupplierProjectsSerializer(
            supplier_projects, many=True, context={"request": request}
        )
        return Response({"status": "succes", "data": serializer.data}, 200)


class InovicePaymentApiView(APIView):
    def post(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(
            ParamsSerializers.InvoicePaymentSerializer, data=request.data
        )
        supplier_id = request.data["supplier_id"]
        payment_amount = float(request.data["payment_amount"])
        notes = request.data.get("notes", "None")
        username = request.data["username"]

        supplier_instance = selectors.get_supplier_instance(supplier_id)

        if payment_amount > supplier_instance.total_amount_payable:
            return Response({"حطأ": "المبلغ المدفوع اكبر من المتبقي "}, 400)

        services.pay_for_supplier(supplier_instance, payment_amount)

        celery_tasks.create_supplier_payment_record.delay(
            supplier_id, payment_amount, notes
        )
        create_transaction_log.delay(
            username=username,
            transaction_data=f"تم تسديد دفعه للمورد {supplier_instance.name} بمبلغ {payment_amount}",
        )

        return Response({"status": "sucess"}, 200)

    def get(Self, request: Request, format=None):
        supplier_id = request.GET.get("supplier_id")
        payments_instances = selectors.get_supplier_payments_instances(supplier_id)

        response_data = pagenator(
            payments_instances, request, OutputSerializers.InvoicePaymentsSerializer
        )
        return Response({"status": "sucess", "data": response_data}, 200)
