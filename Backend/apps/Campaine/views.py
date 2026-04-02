from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Campaine
from .serializers.CampaignSerializers import CampaineSerializer
from .serializers.InputSerializers import CreateCampaineSerializer
from .db_queries.services import create_campaign_service
from .tasks.pagenator import pagenator  # Assuming same pagenator exists


class CampaineListCreateView(APIView):
    def get(self, request):
        return
        campaigns = Campaine.objects.all().order_by("-created_date")
        response_data = pagenator(campaigns, request)
        # Fallback if pagenator is different
        serializer = CampaineSerializer(campaigns, many=True)
        response_data = {
            "data": {"results": serializer.data, "count": campaigns.count()}
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CreateCampaineSerializer(data=request.data)
        if serializer.is_valid():
            try:
                campaign = create_campaign_service(
                    name=serializer.validated_data["name"],
                    client_id=serializer.validated_data["client_id"],
                    items_data=serializer.validated_data["items"],
                )
                output_serializer = CampaineSerializer(campaign)
                return Response(
                    {"data": output_serializer.data}, status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
