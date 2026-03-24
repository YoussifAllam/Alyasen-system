from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from .models.base_project_models import BaseProject, ProjectContracts
from .serializers import InputSerializers, OutputSerializers
from apps.Suppliers.tasks.pagenator import pagenator
from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


class ProjectApiView(APIView):
    def get(self, request: Request, format=None):
        query = request.GET.get("q", "").strip()
        projects = BaseProject.objects.all().order_by("-created_date")
        if query:
            projects = projects.filter(name__icontains=query)

        response_data = pagenator(
            projects, request, OutputSerializers.ProjectSerializer
        )

        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        serializer = InputSerializers.ProjectCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "failed", "errors": serializer.errors}, status=HTTP_400_BAD_REQUEST
            )

        project = serializer.save()

        contracts = request.FILES.getlist("contracts")
        for contract_file in contracts:
            ProjectContracts.objects.create(project=project, contract=contract_file)

        username = request.data.get("username", "Unknown")
        transaction_msg = f"تم أضافة مشروع جديد للنظام '{project.name}'"
        create_transaction_log.delay(transaction_data=transaction_msg, username=username)

        return Response({"status": "success"}, status=HTTP_200_OK)
