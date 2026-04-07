from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .models.base_project_models import BaseProject, ProjectContracts
from .serializers import InputSerializers, OutputSerializers
from .db_queries import selectors, services
from .tasks.pagenator import pagenator

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


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


class ProjectContractsApiView(APIView):
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
        project_id = request.GET.get("project_id")
        target_project = selectors.get_specific_project(project_id)
        serializer = OutputSerializers.RentProjectInfoSerializer(target_project)
        return Response(serializer.data, status=HTTP_200_OK)
