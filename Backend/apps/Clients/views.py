import logging
import traceback

from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.exceptions import NotFound

from .Tasks.pagenator import pagenator
from .models import ClientProjectBalance
from .db_queries import selectors, services
from .serializers import InputSerializers, OutputSerializers, ParamsSerializers
from .Tasks import celery_tasks, client_email_tasks

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


logger = logging.getLogger(__name__)


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


class ClientProjectsApiView(APIView):
    def get(self, request: Request):
        client_id = request.GET.get("client_id")
        CBP_instnaces = selectors.get_client_CBP_instances(client_id)
        response_data = pagenator(
            CBP_instnaces, request, OutputSerializers.CBPSerializer, page_size=4
        )

        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        project_type = request.data.get("project_type")  # campaine , BaseProject
        project_id = request.data.get("project_id")
        client_id = request.data.get("client_id")
        username = request.data.get("username") or "system"

        missing = [
            name
            for name, val in (
                ("project_type", project_type),
                ("project_id", project_id),
                ("client_id", client_id),
            )
            if not val
        ]
        if missing:
            return Response(
                {
                    "status": "faild",
                    "errors": {name: ["This field is required."] for name in missing},
                },
                status=400,
            )

        try:
            client_instance = selectors.get_client_instance(client_id)
            nav_project_type = None

            if project_type == "campaine":
                campaine_instance = selectors.get_campaine_instance(project_id)
                CBP_instance = services.create_CPB_instance(
                    client_instance=client_instance,
                    campaine_instance=campaine_instance,
                )
                services.create_rent_p_instnace(
                    CBP_instance, campaine_instance.total_cost
                )
                nav_project_type = "campaine"
            else:
                base_project_instance = selectors.get_BP_instance(project_id)
                CBP_instance = services.create_CPB_instance(
                    client_instance=client_instance,
                    base_project_instance=base_project_instance,
                )
                if base_project_instance.project_type == "rent":
                    services.create_rent_p_instnace(
                        CBP_instance, base_project_instance.cost
                    )
                else:
                    services.create_sell_ind_p_instnace(
                        CBP_instance, base_project_instance.cost
                    )
                nav_project_type = base_project_instance.project_type

            services.update_client_balance_using_CBP(
                CBP_instance, client_instance, username
            )
        except NotFound:
            raise
        except Exception as exc:
            logger.exception("Failed to link project to client")
            return Response(
                {
                    "status": "faild",
                    "errors": {"server": [str(exc)]},
                    "trace": traceback.format_exc().splitlines()[-5:],
                },
                status=500,
            )

        return Response(
            {
                "status": "success",
                "data": {
                    "cbp_id": CBP_instance.id,
                    "project_type": nav_project_type,
                },
            },
            status=200,
        )


class ResolveCBPNavApiView(APIView):
    """
    GET ?cbp_id=
    Returns canonical project_type for desktop routing (rent / industrial / selling / campaine).
    """

    def get(self, request: Request, format=None):
        cbp_id = request.GET.get("cbp_id")
        if not cbp_id:
            return Response(
                {"status": "faild", "errors": {"cbp_id": ["This field is required."]}},
                status=400,
            )
        try:
            cbp = ClientProjectBalance.objects.select_related(
                "project_fk", "campaine_fk"
            ).get(pk=cbp_id)
        except ClientProjectBalance.DoesNotExist:
            raise NotFound(detail="لا يوجد رصيد مشروع بهذا الكود")

        if cbp.campaine_fk_id:
            nav_type = "campaine"
        elif cbp.project_fk_id:
            nav_type = cbp.project_fk.project_type
        else:
            return Response(
                {"status": "faild", "errors": {"cbp": ["invalid balance row"]}},
                status=400,
            )

        return Response(
            {
                "status": "success",
                "data": {"cbp_id": cbp.id, "project_type": nav_type},
            },
            status=HTTP_200_OK,
        )


class InovicePaymentApiView(APIView):
    def post(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(
            ParamsSerializers.InvoicePaymentSerializer, data=request.data
        )
        project_id = request.data["project_id"]
        project_type = request.data["project_type"]
        payment_amount = float(request.data["payment_amount"])
        payment_method = request.data["payment_type"]
        user_name = request.data["user_name"]

        CPB_instance = selectors.get_client_CPB(project_id, project_type)

        if payment_amount > CPB_instance.remining:
            return Response({"error": "المبلغ المدفوع اكبر من المتبقي "}, 400)

        if payment_method == "check":
            is_cleared = False
        else:
            is_cleared = True
            services.client_payment(
                CPB_instance.client_fk.id, payment_amount, user_name
            )
            services.update_project_balance(CPB_instance, payment_amount)

        serializer = InputSerializers.ProjectPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "faild", "errors": serializer.errors}, status=400
            )
        serializer.save(client_project_balance_fk=CPB_instance, is_cleared=is_cleared)

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

    def patch(self, request: Request, format=None):
        payment_id = request.data["payment_id"]
        user_name = request.data["user_name"]
        payment_instance = selectors.get_payment_instance(payment_id)
        if payment_instance.is_cleared:
            return Response({"error": "الدفعة تم تسويتها بالفعل"}, 400)

        services.client_payment(
            payment_instance.client_project_balance_fk.client_fk.id,
            payment_instance.payment_amount,
            user_name,
        )
        services.update_project_balance(
            payment_instance.client_project_balance_fk, payment_instance.payment_amount
        )
        payment_instance.is_cleared = True
        payment_instance.save()

        return Response({"status": "success"}, 200)


class SendFinancialReportEmailApiView(APIView):
    def post(self, request: Request):
        client_id = request.GET.get("client_id")
        msg, status_code = client_email_tasks.send_financial_report_email(client_id)
        return Response(msg, status=status_code)


class ClientProjectAndCampaingsApiView(APIView):
    def get(self, request: Request):
        projects, campaigns = selectors.get_project_and_campaings()

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
