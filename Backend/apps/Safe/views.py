from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .tasks import pagenator
from .db_queries import selectors
from .serializers import OutputSerializers


class SafeView(APIView):
    def get(self, request: Request, format=None):
        safe_balance = selectors.get_safe_balance()
        return Response({"status": "success", "data": safe_balance}, status=HTTP_200_OK)

    def put(self, request: Request, format=None):
        process = request.data["process"]
        safe_balance = selectors.get_safe_balance()

        if process == "add":
            safe_balance.balance += request.data["amount"]
        elif process == "subtract":
            safe_balance.balance -= request.data["amount"]

        safe_balance.save()
        return Response({"status": "success"}, status=HTTP_200_OK)


class SafeLogsView(APIView):
    def get(self, request: Request, format=None):
        date = request.GET.get("date")
        safe_logs = selectors.get_safe_logs(date=date)
        paginated_response = pagenator.pagenator(safe_logs, request)
        return Response(paginated_response, status=HTTP_200_OK)
