from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .tasks import pagenator
from .db_queries import selectors
from .serializers import InputSerializers, OutputSerializers
from .models import CompanyAssetsAttachments


class CompanyAssetsView(APIView):
    def get(self, request: Request, format=None):
        company_assets = selectors.get_CompanyAssets_instances(request)

        response_data = pagenator.pagenator(
            company_assets, request, OutputSerializers.CompanyAssetsSerializer
        )
        return Response(
            {"status": "success", "data": response_data}, status=HTTP_200_OK
        )

    def post(self, request: Request, format=None):
        serializer = InputSerializers.MachineSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "faild", "errors": serializer.errors}, status=400
            )
        serializer.save()
        return Response({"status": "success"}, status=201)

    def delete(self, request: Request, format=None):
        machine_id = request.data["machine_id"]
        machine_instance = selectors.get_specific_company_asset_instance(machine_id)
        machine_instance.delete()
        return Response({"status": "success"}, status=204)


class CompanyAssetsAttachmentsApiView(APIView):
    def get(self, request: Request, format=None):
        asset_id = request.GET.get("asset_id")
        attachments = selectors.get_CompanyAssetsAttachments_instances(asset_id)
        response_data = pagenator.pagenator(
            attachments, request, OutputSerializers.CompanyAssetsAttachmentsSerializer
        )
        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        asset_id = request.data.get("asset_id")
        attachments = request.FILES.getlist("attachments")

        objs_to_create = []

        for file in attachments:
            objs_to_create.append(
                CompanyAssetsAttachments(asset_id=asset_id, file=file)
            )

        CompanyAssetsAttachments.objects.bulk_create(objs_to_create)

        return Response({"status": "success"}, status=HTTP_200_OK)
