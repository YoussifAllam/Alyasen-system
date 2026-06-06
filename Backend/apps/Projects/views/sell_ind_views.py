from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from ..models.base_project_models import BaseProject, ProjectContracts
from ..serializers import InputSerializers, OutputSerializers
from ..db_queries import selectors, services
from ..tasks.pagenator import pagenator

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log
from apps.Safe.db_queries.services import adjust_safe_balance


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

    def patch(self, request: Request):
        CBP_id = request.data.get("CBP_id")
        target_project = selectors.get_selling_ind_project_using_CBP(CBP_id)
        serializer = InputSerializers.SellingIndustrialProjectUpdateSerializer(
            target_project, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(
                {"status": "failed", "errors": serializer.errors}, status=400
            )
        serializer.save()
        if "selling_price" in request.data:
            services.update_project_info(CBP_id, target_project)
        if "insurance_tax" in request.data:
            try:
                adjust_safe_balance(
                    process="subtract",
                    amount=float(request.data["insurance_tax"]),
                    note=f"تم دفع تأمين لمشروع {target_project.CPB_fk.project_name}",
                    username=request.data["user_name"],
                )
            except ValueError as exc:
                return Response(
                    {"status": "failed", "errors": str(exc)}, status=HTTP_400_BAD_REQUEST
                )
        return Response({"status": "success"}, status=HTTP_200_OK)


class ProjectContractsApiView(APIView):

    def post(self, request: Request, format=None):
        CBP_id = request.data.get("CBP_id")
        attachments = request.FILES.getlist("attachments")

        sell_ind_p_instance = selectors.get_selling_ind_project_using_CBP(CBP_id)

        services.create_sell_ind_p_contracts(sell_ind_p_instance, attachments)

        return Response({"status": "success"}, status=HTTP_200_OK)

    def delete(self, request: Request):
        contract_id = request.data.get("contract_id")
        contract = selectors.get_sell_ind_contract_instnace(contract_id)
        contract.delete()
        return Response({"status": "success"}, status=HTTP_200_OK)


class ProjectGuaranteeChequesApiView(APIView):
    def get(self, request: Request, format=None):
        CBP_id = request.GET.get("CBP_id")
        cheque = selectors.get_sell_ind_guarantee_cheque_using_CBP(CBP_id)
        serializer = (
            OutputSerializers.SellingIndustrialProjectGuaranteeChequesSerializer(cheque)
        )
        return Response(
            {"status": "success", "data": serializer.data}, status=HTTP_200_OK
        )

    def post(self, request: Request, format=None):
        CBP_id = request.data.get("CBP_id")
        sell_ind_p_instance = selectors.get_selling_ind_project_using_CBP(CBP_id)
        serializer = (
            InputSerializers.SellingIndustrialProjectGuaranteeChequesSerializer(
                data=request.data
            )
        )
        if not serializer.is_valid():
            return Response(
                {"status": "failed", "errors": serializer.errors}, status=400
            )
        serializer.save(project=sell_ind_p_instance)
        return Response({"status": "success"}, status=HTTP_200_OK)

    def delete(self, request: Request):
        CBP_id = request.data.get("CBP_id")
        cheque = selectors.get_sell_ind_guarantee_cheque_using_CBP(CBP_id)
        cheque.delete()
        return Response({"status": "success"}, status=HTTP_200_OK)


class ProjectOperationgCost(APIView):
    def get(self, request: Request, format=None):
        CBP_id = request.GET.get("CBP_id")
        target_project = selectors.get_sell_ind_p_operating_costs_using_CBP(CBP_id)
        serializer = OutputSerializers.SellingIndustrialProjectOperationgCostSerializer(
            target_project, many=True
        )
        return Response(
            {"status": "success", "data": serializer.data}, status=HTTP_200_OK
        )

    def post(self, request: Request, format=None):
        CBP_id = request.data.get("CBP_id")
        sell_ind_p_instance = selectors.get_selling_ind_project_using_CBP(CBP_id)
        serializer = InputSerializers.SellingIndustrialProjectOperationgCostSerializer(
            data=request.data
        )
        if not serializer.is_valid():
            return Response(
                {"status": "failed", "errors": serializer.errors}, status=400
            )
        serializer.save(project=sell_ind_p_instance)
        CBP_instance = selectors.get_CBP(CBP_id)
        services.update_client_balance_fields(CBP_instance)
        return Response({"status": "success"}, status=HTTP_200_OK)

    def delete(self, request: Request):
        cost_id = request.data.get("cost_id")
        cost = selectors.get_specific_sell_ind_operating_cost(cost_id)
        cost.delete()
        services.update_client_balance_fields(cost.project.CPB_fk)
        return Response({"status": "success"}, status=HTTP_200_OK)


class ProjectInsuranceTaxApiView(APIView):
    def patch(self, request: Request):
        CBP_id = request.data.get("CBP_id")
        sell_ind_p_instance = selectors.get_selling_ind_project_using_CBP(CBP_id)
        amount = sell_ind_p_instance.insurance_tax
        sell_ind_p_instance.insurance_tax_cleared = True
        sell_ind_p_instance.save()
        adjust_safe_balance(
            process="add",
            amount=float(amount),
            note=f"تم استرداد تأمين لمشروع {sell_ind_p_instance.CPB_fk.project_name}",
            username=request.data["user_name"],
        )
        return Response({"status": "success"}, status=HTTP_200_OK)
