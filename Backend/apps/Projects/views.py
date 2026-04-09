from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .models.base_project_models import BaseProject, ProjectContracts
from .serializers import InputSerializers, OutputSerializers
from .db_queries import selectors, services
from .tasks.pagenator import pagenator

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log
from apps.Safe.tasks.celery_tasks import reduce_safe_balance


class ProjectApiView(APIView):
    def get(self, request: Request, format=None):
        projects = selectors.get_projects(request)
        response_data = pagenator(
            projects, request, OutputSerializers.BaseProjectsNamesSerializer
        )
        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        serializer = InputSerializers.ProjectCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "failed", "errors": serializer.errors},
                status=HTTP_400_BAD_REQUEST,
            )
        project = serializer.save()

        services.update_supplier_balance(request)
        services.create_supplier_project_balance_instance(project.supplier, project)
        username = request.data.get("username", "Unknown")
        transaction_msg = f"تم أضافة مشروع جديد للنظام '{project.name}'"
        create_transaction_log.delay(
            transaction_data=transaction_msg, username=username
        )

        return Response({"status": "success", "id": project.id}, status=HTTP_200_OK)

    def patch(self, request: Request):
        project_id = request.data.get("project_id")
        project = selectors.get_base_project_by_id(project_id)
        services.update_project_status(project)
        return Response({"status": "success"}, status=HTTP_200_OK)


class BaseProjectContractsApiView(APIView):
    def get(self, request: Request, format=None):
        project_id = request.GET.get("project_id")
        contracts = ProjectContracts.objects.filter(project_id=project_id)
        response_data = pagenator(
            contracts, request, OutputSerializers.ProjectContractSerializer
        )
        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        project_id = request.data.get("project_id")
        attachments = request.FILES.getlist("attachments")

        objs_to_create = []

        for file in attachments:
            objs_to_create.append(
                ProjectContracts(project_id=project_id, contract=file)
            )

        ProjectContracts.objects.bulk_create(objs_to_create)

        return Response({"status": "success"}, status=HTTP_200_OK)


class RentProjectsApiView(APIView):
    def get(self, request: Request, format=None):
        CBP_id = request.GET.get("CBP_id")
        target_project = selectors.get_specific_project_using_CBP(CBP_id)
        serializer = OutputSerializers.RentProjectInfoSerializer(target_project)
        return Response(
            {"status": "success", "data": serializer.data}, status=HTTP_200_OK
        )

    def patch(self, request: Request):
        CBP_id = request.data.get("CBP_id")
        target_project = selectors.get_specific_project_using_CBP(CBP_id)
        serializer = InputSerializers.RentProjectsUpdateSerializer(
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
            transaction = f"تم دفع تأمين بملغ {request.data['insurance_tax']} لمشروع {target_project.CPB_fk.project_name}"  # noqa
            reduce_safe_balance.delay(
                request.data["insurance_tax"], transaction, request.data["user_name"]
            )
        return Response({"status": "success"}, status=HTTP_200_OK)


class RentProjectContractsApiView(APIView):

    def post(self, request: Request, format=None):
        CBP_id = request.data.get("CBP_id")
        attachments = request.FILES.getlist("attachments")

        r_p_instance = selectors.get_specific_project_using_CBP(CBP_id)

        services.create_r_p_contracts(r_p_instance, attachments)

        return Response({"status": "success"}, status=HTTP_200_OK)

    def delete(self, request: Request):
        contract_id = request.data.get("contract_id")
        contract = selectors.get_r_contract_instnace(contract_id)
        contract.delete()
        return Response({"status": "success"}, status=HTTP_200_OK)
