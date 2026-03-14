from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .tasks import pagenator, reapir_history_tasks
from .db_queries import selectors
from .serializers import InputSerializers, OutputSerializers

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


class MachineView(APIView):
    def get(self, request: Request, format=None):
        machines = selectors.get_Machines_instances(request)

        response_data = pagenator.pagenator(machines, request, OutputSerializers.MachineSerializer)
        return Response({"status": "success", "data": response_data}, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        serializer = InputSerializers.MachineSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=400)

        tranaction = f"تم اضافة أله{request.data['name']} جديده للنظام"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        serializer.save()
        return Response({"status": "success"}, status=201)

    def delete(self, request: Request, format=None):
        machine_id = request.data["machine_id"]
        machine_instance = selectors.get_specific_machine_instance(machine_id)
        machine_instance.delete()

        tranaction = "تم حذف أله من النظام"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)
        return Response({"status": "success"}, status=204)


class MachineComponentsView(APIView):
    def get(self, request: Request, format=None):
        machine_id = request.GET.get("machine_id")
        machine_companies = selectors.get_machine_components_instances(machine_id)
        response_data = pagenator.pagenator(
            machine_companies, request, OutputSerializers.MachineComponentsSerializer
        )
        return Response({"status": "success", "data": response_data}, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        serializer = InputSerializers.MachineComponentsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=400)
        serializer.save()
        return Response({"status": "success"}, status=201)

    def delete(self, request: Request, format=None):
        machine_component_id = request.data["machine_component_id"]
        machine_component_instance = selectors.get_specific_machine_component_instance(machine_component_id)
        machine_component_instance.delete()
        return Response({"status": "success"}, status=204)


class MachineInfo(APIView):
    def get(self, request: Request, format=None):
        machine_id = request.GET.get("machine_id")
        machine_instance = selectors.get_specific_machine_instance(machine_id)
        serializer = OutputSerializers.MachineInfoSerializer(machine_instance, context={"request": request})
        return Response({"status": "success", "data": serializer.data}, status=HTTP_200_OK)


class MachineRepairHistoryView(APIView):
    def get(self, request: Request, format=None):
        machine_id = request.GET.get("machine_id")
        machine_repair_history = selectors.get_machine_repair_history_instances(machine_id)
        response_data = pagenator.pagenator(
            machine_repair_history, request, OutputSerializers.MachineRepairHistorySerializer
        )
        return Response({"status": "success", "data": response_data}, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        machine_id = request.data["machine_id"]
        machine_instance = selectors.get_specific_machine_instance(machine_id)

        serializer = InputSerializers.MachineRepairHistorySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=400)
        serializer.save(machine=machine_instance)

        reapir_history_tasks.update_machein_last_repair_date(machine_instance, request.data["date"])

        return Response({"status": "success"}, status=HTTP_201_CREATED)

    def delete(self, request: Request, format=None):
        machine_repair_history_id = request.data["machine_repair_history_id"]
        machine_repair_history_instance = selectors.get_specific_machine_repair_history_instance(
            machine_repair_history_id
        )
        machine_repair_history_instance.delete()
        return Response({"status": "success"}, status=HTTP_204_NO_CONTENT)
