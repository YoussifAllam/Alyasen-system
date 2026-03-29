from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .serializers.OutputSerializers import (
    QuotationSerializer,
    QuotationAttachmentsSerializer,
)
from .tasks.pagenator import pagenator
from .db_queries import selectors

from .models import QuotationsAttachments


class QuotationsViewSet(APIView):
    def get(self, request: Request, format=None):
        filtred_quotations = selectors.get_quotations(request)
        response_data = pagenator(filtred_quotations, request, QuotationSerializer)
        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        serializer = QuotationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    def delete(self, request: Request, format=None):
        quotation = selectors.get_specific_quotation(id=request.data["id"])
        quotation.delete()
        return Response({"msg": "تم حذف عرض السعر بنجاح"}, status=HTTP_200_OK)


class QAttchmentsView(APIView):
    def get(self, request: Request, format=None):
        q_id = request.GET.get("q_id")
        filtred_quotations = selectors.get_quotation_attachments(q_id)
        response_data = pagenator(
            filtred_quotations, request, QuotationAttachmentsSerializer
        )
        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        quotation_id = request.data.get("q_id")
        attachments = request.FILES.getlist("attachments")

        objs_to_create = []

        for file in attachments:
            objs_to_create.append(
                QuotationsAttachments(quotation_id=quotation_id, attachment=file)
            )

        QuotationsAttachments.objects.bulk_create(objs_to_create)
        return Response({"msg": "تم الحفظ بنجاح"}, status=HTTP_200_OK)
