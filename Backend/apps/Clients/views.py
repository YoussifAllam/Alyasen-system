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

        response_data = pagenator(
            filtred_transactions, request, OutputSerializers.ClientsSerializer
        )

        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        serializer = InputSerializers.ClientsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "faild", "errors": serializer.errors}, status=400
            )
        serializer.save()

        tranaction = "تم أضافة عميل جديد للنظام"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response({"status": "success"}, status=201)

    def patch(self, request: Request, format=None):
        client_id = request.data["client_id"]
        client_instance = selectors.get_client_instance(client_id)
        serializer = InputSerializers.ClientUpdateSerializer(
            client_instance, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(
                {"status": "faild", "errors": serializer.errors}, status=400
            )
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


class ClientProjectAndCampaingsApiView(APIView):
    def get(self, request: Request):
        client_id = request.GET.get("client_id")
        projects, campaigns = selectors.get_client_project_and_campaings(client_id)

        projects_serializer = OutputSerializers.BaseProjectSerializer(
            projects, many=True
        )
        campaigns_serializer = OutputSerializers.CampaineSerializer(
            campaigns, many=True
        )

        response_data = {
            "campaigns": campaigns_serializer.data,
            "projects": projects_serializer.data,
        }
        return Response(response_data, status=HTTP_200_OK)


class InovicePaymentApiView(APIView):
    def post(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(
            ParamsSerializers.InvoicePaymentSerializer, data=request.data
        )
        project_id = request.data["project_id"]
        project_type = request.data["project_type"]
        payment_amount = float(request.data["payment_amount"])

        project_instance = selectors.get_client_CPB(project_id, project_type)

        if payment_amount > project_instance.remining:
            return Response({"حطأ": "المبلغ المدفوع اكبر من المتبقي "}, 400)

        services.client_payment(project_instance, payment_amount)
        services.update_project_balance(project_instance, payment_amount)

        serializer = InputSerializers.ProjectPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "faild", "errors": serializer.errors}, status=400
            )
        serializer.save(
            client_fk=project_instance.client_fk, project_fk=project_instance.project_fk
        )

        return Response({"status": "sucess"}, 200)

    def get(Self, request: Request, format=None):
        # client_id = request.GET.get("client_id")
        project_id = request.GET.get("project_id")
        project_type = request.GET.get("type")
        payments_instances = selectors.get_client_payments_instances_by_CPB(
            project_id, project_type
        )

        response_data = pagenator(
            payments_instances, request, OutputSerializers.InvoicePaymentsSerializer
        )
        return Response(response_data, 200)


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
