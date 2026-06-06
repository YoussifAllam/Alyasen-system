from django.db import transaction
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from .db_queries import selectors, services
from .serializers import InputSerializers, OutputSerializers
from .tasks import pagenator, log_tasks


class CompanyAssetsView(APIView):
    def get(self, request: Request, format=None):
        company_assets = selectors.get_CompanyAssets_instances(request)
        summary = selectors.get_company_assets_summary(company_assets)
        response_data = pagenator.pagenator(
            company_assets, request, OutputSerializers.CompanyAssetsSerializer
        )
        response_data["summary"] = summary
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
        return Response({"status": "success", "id": serializer.instance.id}, status=201)

    def patch(self, request: Request, format=None):
        asset_id = request.data.get("id") or request.data.get("machine_id")
        if not asset_id:
            return Response(
                {"status": "faild", "errors": "معرّف الأصل مطلوب"}, status=400
            )
        instance = selectors.get_specific_company_asset_instance(asset_id)
        serializer = InputSerializers.MachineSerializer(
            instance, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(
                {"status": "faild", "errors": serializer.errors}, status=400
            )
        services.update_company_asset(
            instance=instance, validated_data=serializer.validated_data
        )
        return Response(
            {
                "status": "success",
                "data": OutputSerializers.CompanyAssetsSerializer(instance).data,
            },
            status=HTTP_200_OK,
        )

    def delete(self, request: Request, format=None):
        asset_id = request.data.get("machine_id") or request.data.get("id")
        machine_instance = selectors.get_specific_company_asset_instance(asset_id)
        machine_instance.delete()
        return Response({"status": "success"}, status=HTTP_204_NO_CONTENT)


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
        if not asset_id:
            return Response(
                {"status": "faild", "errors": "معرّف الأصل مطلوب"}, status=400
            )
        if not attachments:
            return Response(
                {"status": "faild", "errors": "لم يتم إرسال مرفقات"}, status=400
            )
        services.create_asset_attachments(asset_id=asset_id, files=attachments)
        return Response({"status": "success"}, status=HTTP_200_OK)
