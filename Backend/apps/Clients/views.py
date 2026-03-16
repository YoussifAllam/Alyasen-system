from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .Tasks.pagenator import pagenator
from .db_queries import selectors, services
from .serializers import InputSerializers, OutputSerializers, ParamsSerializers
from .Tasks import celery_tasks

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


class ClientsApiView(APIView):
    def get(self, request: Request, format=None):
        filtred_transactions = selectors.get_clients(request)

        response_data = pagenator(filtred_transactions, request, OutputSerializers.ClientsSerializer)

        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        serializer = InputSerializers.ClientsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=400)
        serializer.save()

        tranaction = "تم أضافة عميل جديد للنظام"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response({"status": "success"}, status=201)

    def patch(self, request: Request, format=None):
        client_id = request.data["client_id"]
        client_instance = selectors.get_client_instance(client_id)
        serializer = InputSerializers.ClientUpdateSerializer(client_instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=400)
        serializer.save()

        tranaction = "تم تحديث بيانات العميل"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response({"status": "success"}, status=200)
        
class ClientInfoApiView(APIView):
    def get(self, request: Request, format=None):
        client_id = request.GET.get("id")
        supplier_instance = selectors.get_client_instance(client_id)
        serializer = OutputSerializers.ClientsSerializer(
            supplier_instance, many=False, context={"request": request}
        )
        return Response({"status": "succes", "data": serializer.data}, 200)

# class ClientPaymentsApiView(APIView):
#     def post(self, request: Request, format=None):
#         ParamsSerializers.validate_serializer(ParamsSerializers.InvoicePaymentSerializer, data=request.data)
#         client_id = request.data["client_id"]
#         payment_amount = int(request.data["payment_amount"])

#         client_instance = selectors.get_client_instance(client_id)

#         if payment_amount > client_instance.total_remaining_balance_owed_to_us:
#             return Response({"حطأ": "المبلغ المدفوع اكبر من المتبقي "}, 400)

#         services.update_client_balance_after_payment(client_instance, payment_amount)
#         username = request.data["username"]
#         notes = request.data.get("notes", "None")
#         celery_tasks.create_client_payment_invoice_record.delay(client_instance.id, payment_amount, notes)
#         create_transaction_log.delay(
#             username=username,
#             transaction_data=f"تم تسديد دفعه من العميل {client_instance.name} بمبلغ {payment_amount}",
#         )

#         return Response({"status": "sucess"}, 200)

#     def get(Self, request: Request, format=None):
#         client_id = request.GET.get("client_id")
#         payments_instances = selectors.get_client_payments_instances(client_id)

#         response_data = pagenator(payments_instances, request, OutputSerializers.ClientPaymentsSerializer)
#         return Response({"status": "sucess", "data": response_data}, 200)

# class ClientStatementEmailView(APIView):
#     def post(self, request: Request, format=None):
#         client_id = request.data.get("client_id")
#         start_date = request.data.get("start_date")
#         end_date = request.data.get("end_date")

#         if not all([client_id, start_date, end_date]):
#             return Response({"status": "error", "message": "Missing required fields"}, status=400)

#         from .Tasks.client_email_tasks import send_client_statement_email
#         result = send_client_statement_email(client_id, start_date, end_date)
        
#         status_code = 200 if result["status"] == "success" else 400
#         return Response(result, status=status_code)
