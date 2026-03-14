from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .tasks.pagenator import pagenator
from .db_queries import selectors, services
from .serializers import InputSerializers, OutputSerializers
from .tasks import worker_tasks, salary_report_tasks

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


class WorkersView(APIView):
    def get(self, request: Request):
        workers_inatances = selectors.get_workers(request)
        response_data = pagenator(workers_inatances, request, OutputSerializers.WorkersSerializer)
        return Response({"status": "success", "data": response_data}, status=HTTP_200_OK)

    def post(self, request: Request):
        serializer = InputSerializers.WorkersSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=400)
        serializer.save()

        tranaction = "تم اضافة موظف جديد للنظام"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response({"status": "success"}, status=HTTP_201_CREATED)

    def delete(self, request: Request):
        worker_id = request.data["worker_id"]
        worker_instance = selectors.get_specific_worker_instance(worker_id)
        worker_instance.delete()

        tranaction = f"تم حذف موظف {worker_instance.name} من النظام"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response({"status": "success"}, status=HTTP_204_NO_CONTENT)


class WorkerInfoView(APIView):
    def get(self, request: Request):
        worker_id = request.GET["worker_id"]
        worker_instance = selectors.get_specific_worker_instance(worker_id)
        serializer = OutputSerializers.WorkersInfoSerializer(
            worker_instance, many=False, context={"request": request}
        )
        return Response({"status": "success", "data": serializer.data}, status=HTTP_200_OK)

    def patch(self, request: Request):
        worker_id = request.data["worker_id"]
        worker_instance = selectors.get_specific_worker_instance(worker_id=worker_id)
        serializer = InputSerializers.WorkerInfoUpdateSerializer(
            worker_instance, data=request.data, partial=True, context={"request": request}
        )

        if not serializer.is_valid():
            return Response({"message": "خطأ", "errors": serializer.errors}, status=HTTP_400_BAD_REQUEST)

        tranaction = f"تم تعديل بيانات الموظف : {worker_instance.name}"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        serializer.save()
        worker_tasks.update_worker_balance(worker_instance)

        return Response(
            {"message": "تم تعديل بيانات الموظف بنجاح", "data": serializer.data}, status=HTTP_200_OK
        )


class WorkerAbsenceView(APIView):
    def get(self, request: Request):
        """
        Get all absence records or filter by worker/date
        """
        worker_id = request.GET.get("worker_id")

        absences_days_instances = selectors.get_absences_days(worker_id=worker_id)
        response_data = pagenator(absences_days_instances, request, OutputSerializers.WorkerAbsenceSerializer)
        return Response({"status": "success", "data": response_data}, status=HTTP_200_OK)

    def post(self, request: Request):
        worker_id = request.data["worker_id"]
        worker_instance = selectors.get_specific_worker_instance(worker_id)

        serializer = InputSerializers.WorkerAbsenceCreateSerializer(
            data=request.data, context={"worker_instance": worker_instance}
        )

        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=HTTP_400_BAD_REQUEST)
        serializer.save(worker=worker_instance)

        user_name = request.data["username"]
        worker_tasks.update_worker_total_days_of_absence(worker_instance, "أضافة", user_name)

        return Response({"status": "success"}, status=HTTP_201_CREATED)

    def delete(self, request: Request):
        absence_id = request.data["absence_id"]
        absence_instance = selectors.get_specific_absence_instance(absence_id)
        worker_instance = absence_instance.worker

        absence_instance.delete()

        user_name = request.data["username"]
        worker_tasks.update_worker_total_days_of_absence(worker_instance, "حذف", user_name)

        return Response({"status": "success"}, status=HTTP_204_NO_CONTENT)

    def patch(self, request: Request):
        worker_id = request.data["worker_id"]
        is_in_vacation = request.data["is_in_vacation"]
        worker_instance = selectors.get_specific_worker_instance(worker_id=worker_id)
        worker_instance.is_in_vacation = is_in_vacation
        worker_instance.save()

        return Response({"status": "success"}, status=HTTP_200_OK)


class DeductionsView(APIView):
    def get(self, request: Request):
        worker_id = request.GET["worker_id"]
        worker_deductions_instance = selectors.get_worker_deductions_instance(worker_id)
        data = pagenator(worker_deductions_instance, request, OutputSerializers.WorkerDeductionsSerializer, 4)
        return Response({"status": "success", "data": data}, status=HTTP_200_OK)

    def post(self, request: Request):
        worker_id = request.data["worker_id"]
        worker_instance = selectors.get_specific_worker_instance(worker_id)

        serializer = InputSerializers.WorkerDeductionCreateSerializer(
            data=request.data, context={"worker_instance": worker_instance}
        )

        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=HTTP_400_BAD_REQUEST)
        serializer.save(worker=worker_instance)

        user_name = request.data["username"]
        deduction_amount = float(request.data["deduction_amount"])
        worker_tasks.update_worker_deduction_balance(worker_instance, "أضافة", user_name, deduction_amount)

        return Response({"status": "success"}, status=HTTP_201_CREATED)

    def delete(self, request: Request):
        deduction_id = request.data["deduction_id"]
        deduction_instance = selectors.get_specific_deduction_instance(deduction_id)

        worker_instance = deduction_instance.worker
        deduction_amount = deduction_instance.deduction_amount

        deduction_instance.delete()

        user_name = request.data["username"]
        worker_tasks.update_worker_deduction_balance(worker_instance, "حذف", user_name, deduction_amount)

        return Response({"status": "success"}, status=HTTP_204_NO_CONTENT)


class WorkerAdvanceView(APIView):
    def get(self, request: Request):
        worker_id = request.GET["worker_id"]
        worker_deductions_instance = selectors.get_worker_sdvances_instance(worker_id)
        data = pagenator(worker_deductions_instance, request, OutputSerializers.WorkerAdvanceSerializer, 4)
        return Response({"status": "success", "data": data}, status=HTTP_200_OK)

    def post(self, request: Request):
        worker_id = request.data["worker_id"]
        worker_instance = selectors.get_specific_worker_instance(worker_id)

        serializer = InputSerializers.WorkerAdvanceCreateSerializer(
            data=request.data, context={"worker_instance": worker_instance}
        )

        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=HTTP_400_BAD_REQUEST)
        advance_instance = serializer.save(worker=worker_instance)

        user_name = request.data["username"]
        advance_amount = float(request.data["advance_amount"])
        advance_date = request.data["advance_date"]
        worker_tasks.update_worker_advance_balance(worker_instance, "أضافة", user_name, advance_amount)
        services.create_workers_paid_salary_instance(
            worker_instance, advance_date, advance_amount, advance_instance
        )

        return Response({"status": "success"}, status=HTTP_201_CREATED)

    def delete(self, request: Request):
        advance_id = request.data["advance_id"]
        advance_instance = selectors.get_specific_advance_instance(advance_id)

        worker_instance = advance_instance.worker
        advance_amount = advance_instance.advance_amount
        advance_id = advance_instance.id
        advance_instance.delete()

        services.delete_workers_paid_salary_instance(advance_id)

        user_name = request.data["username"]
        worker_tasks.update_worker_advance_balance(worker_instance, "حذف", user_name, advance_amount)

        return Response({"status": "success"}, status=HTTP_204_NO_CONTENT)


class WorkerAttendanceView(APIView):
    def post(self, request: Request):
        worker_id = request.data["worker_id"]
        transaction = request.data["transaction"]
        worker_instance = selectors.get_specific_worker_instance(worker_id)
        worker_tasks.update_worker_attendance(worker_instance, transaction)
        return Response({"status": "success"}, status=HTTP_201_CREATED)

    def get(self, request: Request):
        worker_id = request.GET["worker_id"]
        worker_attendance_instance = selectors.get_worker_all_attendance_instances(worker_id)
        data = pagenator(worker_attendance_instance, request, OutputSerializers.WorkerAttendanceSerializer)
        return Response({"status": "success", "data": data}, status=HTTP_200_OK)


class FinishWorkerShiftView(APIView):
    def post(self, request: Request):
        worker_id = request.data["worker_id"]
        worker_instance = selectors.get_specific_worker_instance(worker_id)
        worker_tasks.finish_worker_shift(worker_instance)

        return Response({"status": "success"}, status=HTTP_201_CREATED)


class WorkerAlternativesView(APIView):
    def get(self, request: Request):
        worker_id = request.GET["worker_id"]
        worker_alternatives_instance = selectors.get_worker_alternatives_instances(worker_id)
        data = pagenator(
            worker_alternatives_instance, request, OutputSerializers.WorkerAlternativesSerializer
        )
        return Response({"status": "success", "data": data}, status=HTTP_200_OK)

    def post(self, request: Request):
        worker_id = request.data["worker_id"]
        worker_instance = selectors.get_specific_worker_instance(worker_id)

        serializer = InputSerializers.WorkerAlternativesCreateSerializer(
            data=request.data, context={"worker": worker_instance}
        )

        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=HTTP_400_BAD_REQUEST)
        serializer.save(worker=worker_instance)

        user_name = request.data["username"]
        alternative_amount = float(request.data["amount"])
        worker_tasks.update_worker_alternative_balance(
            worker_instance, "أضافة", user_name, alternative_amount
        )

        return Response({"status": "success"}, status=HTTP_201_CREATED)

    def delete(self, request: Request):
        alternative_id = request.data["alternative_id"]
        alternative_instance = selectors.get_specific_alternative_instance(alternative_id)

        worker_instance = alternative_instance.worker
        alternative_amount = alternative_instance.amount
        alternative_instance.delete()

        user_name = request.data["username"]
        worker_tasks.update_worker_alternative_balance(worker_instance, "حذف", user_name, alternative_amount)

        return Response({"status": "success"}, status=HTTP_204_NO_CONTENT)


class WorkerSalaryReport(APIView):
    def get(self, request: Request):
        worker_id = request.GET["worker_id"]
        worker_instance = selectors.get_specific_worker_instance(worker_id)
        data = salary_report_tasks.get_worker_salary_report(worker_instance)
        return Response({"status": "success", "data": data}, status=HTTP_200_OK)
