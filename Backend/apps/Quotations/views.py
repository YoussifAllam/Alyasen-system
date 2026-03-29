from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .serializers.OutputSerializers import QuotationSerializer
from .tasks.pagenator import pagenator
from .db_queries import selectors


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
