from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .serializers import OutputSerializers
from .db_queries import selectors
from .db_backup import build_sqlite_backup_response

from .tasks import (
    expenses_graph_tasks,
    top_lists_tasks,
    # inventory_levels_tasks,
    # performance_graph_tasks,
    users_tasks,
    insurance_tax_tasks,
    guarantee_checks_tasks,
)


class ExpensesGraphApiView(APIView):
    def get(self, request: Request, format=None):
        expenses_analysis = (
            expenses_graph_tasks.ExpensesAnalysisService.get_expenses_breakdown()
        )

        return Response(
            {"status": "success", "data": expenses_analysis}, status=HTTP_200_OK
        )


class TopListsDataApiView(APIView):
    def get(self, request: Request):
        top_lists = top_lists_tasks.get_top_data()
        return Response({"status": "success", "data": top_lists}, status=HTTP_200_OK)


class UsersStutsApiView(APIView):
    def get(self, request: Request, format=None):
        users_analysis = users_tasks.get_users_status()

        return Response(
            {"status": "success", "data": users_analysis}, status=HTTP_200_OK
        )


class UsersApiView(APIView):
    def get(self, request: Request, format=None):
        is_approvid = request.GET.get("is_approvid")
        users = users_tasks.get_users(is_approvid)
        serializer = OutputSerializers.UserSerializer(users, many=True)
        return Response(
            {"status": "success", "data": serializer.data}, status=HTTP_200_OK
        )

    def post(self, request: Request, format=None):
        user_uuid = request.data["user_uuid"]
        user_instance = selectors.get_user_instance(user_uuid)
        user_instance.is_approvid = True
        user_instance.save()
        return Response({"status": "success"}, status=201)

    def delete(self, request: Request, format=None):
        user_uuid = request.data["user_uuid"]
        user_instance = selectors.get_user_instance(user_uuid)
        user_instance.delete()
        return Response({"status": "success"}, status=204)


class UpcomingInsuranceTaxApiView(APIView):
    def get(self, request: Request, format=None):
        data = insurance_tax_tasks.get_upcoming_insurance_tax_projects()
        return Response({"status": "success", "data": data}, status=HTTP_200_OK)


class GuaranteeChecksApiView(APIView):
    def get(self, request: Request, format=None):
        data = guarantee_checks_tasks.get_nearest_guarantee_checks()
        return Response({"status": "success", "data": data}, status=HTTP_200_OK)


class DatabaseBackupApiView(APIView):
    def get(self, request: Request, format=None):
        try:
            return build_sqlite_backup_response()
        except FileNotFoundError as exc:
            return Response({"status": "faild", "errors": str(exc)}, status=404)
        except ValueError as exc:
            return Response({"status": "faild", "errors": str(exc)}, status=400)
        except Exception:
            return Response(
                {"status": "faild", "errors": "تعذر إنشاء نسخة احتياطية من قاعدة البيانات"},
                status=500,
            )
