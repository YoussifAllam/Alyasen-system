from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .tasks import pagenator
from .db_queries import selectors, services
from .serializers import OutputSerializers


class SafeView(APIView):
    def get(self, request: Request, format=None):
        summary = selectors.get_safe_summary()
        return Response({"status": "success", "data": summary}, status=HTTP_200_OK)

    def put(self, request: Request, format=None):
        process = request.data.get("process")
        amount = request.data.get("amount")
        note = request.data.get("note", "")
        username = request.data.get("username", "")

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return Response(
                {"status": "faild", "errors": "المبلغ غير صالح"},
                status=400,
            )

        try:
            balance = services.adjust_safe_balance(
                process=process,
                amount=amount,
                note=note,
                username=username,
            )
        except ValueError as exc:
            return Response({"status": "faild", "errors": str(exc)}, status=400)

        summary = selectors.get_safe_summary()
        summary["balance"] = balance
        return Response({"status": "success", "data": summary}, status=HTTP_200_OK)


class SafeLogsView(APIView):
    def get(self, request: Request, format=None):
        date = request.GET.get("date")
        date_from = request.GET.get("date_from")
        date_to = request.GET.get("date_to")
        operation_type = request.GET.get("operation_type")
        search = request.GET.get("search")

        safe_logs = selectors.get_safe_logs(
            date=date,
            date_from=date_from,
            date_to=date_to,
            operation_type=operation_type,
            search=search,
        )
        paginated_response = pagenator.pagenator(safe_logs, request)
        return Response(paginated_response, status=HTTP_200_OK)
