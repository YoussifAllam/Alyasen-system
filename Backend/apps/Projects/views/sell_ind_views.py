from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from ..models.base_project_models import BaseProject, ProjectContracts
from ..serializers import InputSerializers, OutputSerializers
from ..db_queries import selectors, services
from ..tasks.pagenator import pagenator

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log
from apps.Safe.tasks.celery_tasks import reduce_safe_balance, increase_safe_balance


class ProjectInfoApiView(APIView):
    def get(self, request: Request, format=None):
        CBP_id = request.GET.get("CBP_id")
        target_project = selectors.get_selling_ind_project_using_CBP(CBP_id)
        serializer = OutputSerializers.SellingIndustrialProjectDetailsSerializer(
            target_project
        )
        return Response(
            {"status": "success", "data": serializer.data}, status=HTTP_200_OK
        )

    # def patch(self, request: Request):
    #     CBP_id = request.data.get("CBP_id")
    #     target_project = selectors.get_specific_project_using_CBP(CBP_id)
    #     serializer = InputSerializers.RentProjectsUpdateSerializer(
    #         target_project, data=request.data, partial=True
    #     )
    #     if not serializer.is_valid():
    #         return Response(
    #             {"status": "failed", "errors": serializer.errors}, status=400
    #         )
    #     serializer.save()
    #     if "selling_price" in request.data:
    #         services.update_project_info(CBP_id, target_project)
    #     if "insurance_tax" in request.data:
    #         transaction = f"تم دفع تأمين بملغ {request.data['insurance_tax']} لمشروع {target_project.CPB_fk.project_name}"  # noqa
    #         reduce_safe_balance.delay(
    #             request.data["insurance_tax"], transaction, request.data["user_name"]
    #         )
    #     return Response({"status": "success"}, status=HTTP_200_OK)
