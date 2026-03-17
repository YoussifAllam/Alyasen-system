from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
# from .tasks.pagenator import pagenator
from .db_queries import selectors


# class TransactionViewSet(APIView):
#     def get(self, request: Request, format=None):
#         filtred_transactions = selectors.get_transactions(request)

#         response_data = pagenator(filtred_transactions, request)

#         return Response(response_data, status=HTTP_200_OK)
