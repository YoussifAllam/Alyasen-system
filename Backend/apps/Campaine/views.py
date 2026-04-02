from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from .models import Campaine
from .serializers import OutputSerializers, InputSerializers
from .db_queries import selectors, services
from .tasks.pagenator import pagenator

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


class CampaineListCreateView(APIView):
    def get(self, request):
        campaigns = selectors.get_all_campaigns()
        response_data = pagenator(
            campaigns, request, OutputSerializers.CampaineSerializer
        )
        return Response(response_data, status=status.HTTP_200_OK)

    @transaction.atomic
    def post(self, request):
        serializer = InputSerializers.CampaineSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": "success"},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"status": "error", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
