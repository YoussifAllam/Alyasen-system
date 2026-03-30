from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .serializers import OutputSerializers
from .db_queries import selectors

from .tasks import (
    expenses_graph_tasks,
    top_lists_tasks,
    # inventory_levels_tasks,
    # performance_graph_tasks,
    users_tasks,
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


# class TopListsDataApiView(APIView):
#     def get(self, request: Request, format=None):
#         top_lists = top_lists_tasks.get_top_data()

#         return Response({"status": "success", "data": top_lists}, status=HTTP_200_OK)


# class InventoryMaterialsLevelApiView(APIView):
#     def get(self, request: Request, format=None):
#         lowest_M_in_quantity = (
#             inventory_levels_tasks.MaterialInventoryService.get_lowest_quantity_materials()
#         )

#         return Response(
#             {"status": "success", "data": lowest_M_in_quantity}, status=HTTP_200_OK
#         )


# class PerformanceGraphApiView(APIView):
#     def get(self, request: Request, format=None):
#         performance_analysis = (
#             performance_graph_tasks.PerformanceAnalysisService.get_current_year_performance()
#         )

#         return Response(
#             {"status": "success", "data": performance_analysis}, status=HTTP_200_OK
#         )


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
