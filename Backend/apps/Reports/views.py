from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

# from .Tasks.pagenator import pagenator
from .db_queries import selectors
from .tasks import date_format


class DailyReportApiView(APIView):
    def get(self, request: Request, format=None):
        start_date = request.GET.get("start_date", "")
        end_date = start_date
        flags_list = request.GET.getlist("flags_list", "")

        json_report = selectors.get_reports(start_date, end_date, flags_list)

        return Response({"status": "success", "data": json_report}, status=HTTP_200_OK)


class MonthReportApiView(APIView):
    def get(self, request: Request, format=None):
        start_date = request.GET.get("month", "")
        year = request.GET.get("year", "")
        flags_list = request.GET.getlist("flags_list", "")

        start_date, end_date = date_format.get_month_start_end(int(start_date), int(year))
        print(start_date, end_date)

        json_report = selectors.get_reports(start_date, end_date, flags_list)

        return Response({"status": "success", "data": json_report}, status=HTTP_200_OK)


class YearReportApiView(APIView):
    def get(self, request: Request, format=None):
        start_date = request.GET.get("start_date", "")
        end_date = request.GET.get("end_date", "")
        flags_list = request.GET.getlist("flags_list", "")

        json_report = selectors.get_reports(start_date, end_date, flags_list)

        return Response({"status": "success", "data": json_report}, status=HTTP_200_OK)
