from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from apps.Safe.tasks.celery_tasks import reduce_safe_balance

from .tasks.pagenator import pagenator
from .db_queries import selectors
from .serializers import InputSerializers


class ExpensesApiView(APIView):
    def get(self, request: Request, format=None):
        filtred_transactions = selectors.get_expenses_instances(request)

        response_data = pagenator(filtred_transactions, request)

        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        serializer = InputSerializers.ExpensesSerializer(data=request.data)
        if serializer.is_valid():
            expense = serializer.save()
            username = request.data.get("user_name") or request.data.get("username") or "system"
            transaction = f"تم تسجيل مصروف: {expense.transaction} بمبلغ {expense.amount}"
            reduce_safe_balance.delay(expense.amount, transaction, username)
            return Response({"status": "success"}, status=HTTP_200_OK)

        return Response({"status": "faild", "errors": serializer.errors}, status=400)


class ExpensesSummeryApiView(APIView):
    def get(self, request: Request, format=None):
        filtred_transactions = selectors.get_expenses_stats()

        response_data = {"status": "success", "data": filtred_transactions}

        return Response(response_data, status=HTTP_200_OK)
