from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .Tasks.pagenator import pagenator
from .db_queries import selectors, services
from .serializers import InputSerializers, OutputSerializers, ParamsSerializers
from .Tasks import celery_tasks, materials_tasks

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


class ClientsApiView(APIView):
    def get(self, request: Request, format=None):
        filtred_transactions = selectors.get_clients(request)

        response_data = pagenator(filtred_transactions, request, OutputSerializers.ClientsSerializer)

        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        serializer = InputSerializers.ClientsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=400)
        serializer.save()

        tranaction = "تم أضافة عميل جديد للنظام"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response({"status": "success"}, status=201)

    def patch(self, request: Request, format=None):
        client_id = request.data["client_id"]
        client_instance = selectors.get_client_instance(client_id)
        serializer = InputSerializers.ClientUpdateSerializer(client_instance, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=400)
        serializer.save()

        tranaction = "تم تحديث بيانات العميل"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response({"status": "success"}, status=200)
        


class ClientInfoApiView(APIView):
    def get(self, request: Request, format=None):
        client_id = request.GET.get("id")
        supplier_instance = selectors.get_client_instance(client_id)
        serializer = OutputSerializers.ClientsSerializer(
            supplier_instance, many=False, context={"request": request}
        )
        return Response({"status": "succes", "data": serializer.data}, 200)


class ClientInovicesApiView(APIView):
    def get(self, request: Request, format=None):
        client_id = request.GET.get("client_id")
        invoices_instances = selectors.get_client_invoices_instance(client_id)
        response_data = pagenator(invoices_instances, request, OutputSerializers.InvocesSerializer, 13)
        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        client_id = request.data["client_id"]
        client_instance = selectors.get_client_instance(client_id)
        serializer = InputSerializers.InvoicesSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=400)
        invoice_instance = serializer.save(client=client_instance)

        tranaction = f"تم اضافة فاتورة رقم {invoice_instance.invoice_number} للعميل {client_instance.name}"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response({"status": "success" , "invoice_number": invoice_instance.invoice_number}, status=201)

    def delete(self, request: Request, format=None):
        invoice_num = request.data["invoice_num"]
        invoice_instance = selectors.get_invoices_instance(invoice_num)
        invoice_instance.delete()

        tranaction = (
            f"تم حذف فاتورة رقم {invoice_instance.invoice_number} من العميل {invoice_instance.client.name}"
        )
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response({"status": "success"}, status=HTTP_204_NO_CONTENT)

    def patch(self, request: Request, format=None):
        client_id = request.data["client_id"]
        invoice_total_amount = float(request.data["invoice_total_amount"])
        paid_amount = float(request.data["paid_amount"])

        client_instance = selectors.get_client_instance(client_id)
        client_instance.total_balance_owed_to_us += invoice_total_amount
        client_instance.total_remaining_balance_owed_to_us += invoice_total_amount - paid_amount
        client_instance.total_paid_amount += paid_amount
        client_instance.save()

        invoice_num = request.data["invoice_num"]
        invoice_instance = selectors.get_invoices_instance(invoice_num)
        invoice_instance.invoice_total_amount += invoice_total_amount
        invoice_instance.save()

        services.create_client_payment_invoice_record(client_instance, paid_amount)



        return Response({"status": "success"}, status=200)


class ClientPaymentsApiView(APIView):
    def post(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(ParamsSerializers.InvoicePaymentSerializer, data=request.data)
        client_id = request.data["client_id"]
        payment_amount = int(request.data["payment_amount"])

        client_instance = selectors.get_client_instance(client_id)

        if payment_amount > client_instance.total_remaining_balance_owed_to_us:
            return Response({"حطأ": "المبلغ المدفوع اكبر من المتبقي "}, 400)

        services.update_client_balance_after_payment(client_instance, payment_amount)
        username = request.data["username"]
        notes = request.data.get("notes", "None")
        celery_tasks.create_client_payment_invoice_record.delay(client_instance.id, payment_amount, notes)
        create_transaction_log.delay(
            username=username,
            transaction_data=f"تم تسديد دفعه من العميل {client_instance.name} بمبلغ {payment_amount}",
        )

        return Response({"status": "sucess"}, 200)

    def get(Self, request: Request, format=None):
        client_id = request.GET.get("client_id")
        payments_instances = selectors.get_client_payments_instances(client_id)

        response_data = pagenator(payments_instances, request, OutputSerializers.ClientPaymentsSerializer)
        return Response({"status": "sucess", "data": response_data}, 200)


class InvoiceMaterialsApiView(APIView):
    def post(self, request: Request, format=None):
        invoice_num = request.data["invoice_num"]
        material_id = request.data["material_id"]
        req_qty_of_mixture = request.data["quantity_in_unit"]
        invoice_instance = selectors.get_invoices_instance(invoice_num)
        material_instnace = selectors.get_specific_material_instance(material_id)

        if selectors.check_if_invoice_has_this_m(invoice_num, material_instnace):
            return Response({"خطأ": "هذا الصنف موجودة بالفاتورة"}, status=400)

        status, message = materials_tasks.check_material_availability(
            material_instnace, float(req_qty_of_mixture)
        )
        if not status:
            return Response({"خطأ": message}, status=400)

        serializer = InputSerializers.InvoiceMaterialsSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"خطا": serializer.errors}, status=400)

        serializer.save(invoice=invoice_instance, material=material_instnace)
        
        return Response(
            {
                "status": "success",
            },
            status=201,
        )

    def delete(self, request: Request, format=None):
        material_id = request.data["mix_id"]
        mixture_instance = selectors.get_specific_invoice_mixture_instance(material_id)
        mixture_total_price = mixture_instance.total_price
        mixture_instance.delete()

        invoice_num = request.data["invoice_num"]
        invoice_instance = selectors.get_invoices_instance(invoice_num)

        invoice_total_amount = services.decrease_invoice_total_amount(invoice_instance, mixture_total_price)
        return Response(
            {"status": "success", "data": {"invoice_total_amount": invoice_total_amount}},
            status=HTTP_204_NO_CONTENT,
        )

    def get(self, request: Request, format=None):
        invoice_num = request.GET.get("invoice_num")
        materials_instances = selectors.get_invoice_mixtures_instances(invoice_num)
        response_data = pagenator(materials_instances, request, OutputSerializers.InvoiceMaterialsSerializer)
        return Response({"status": "sucess", "data": response_data}, 200)


class MoveInvoiceMaterialsFromWarehouseAPIView(APIView):
    def post(self, request: Request):

        invoice_num = request.data["invoice_num"]

        invoice_instance = selectors.get_invoices_instance(invoice_num)

        if invoice_instance.is_moved_to_warehouse:
            return Response({"خطأ": "هذه الفاتورة تم تحويلها من قبل"}, status=400)

        success, production_message = materials_tasks.create_material_production_from_invoice(invoice_instance)
        if not success:
            return Response({"خطأ": production_message}, status=400)

        invoice_instance.is_moved_to_warehouse = True
        invoice_instance.save()

        return Response({"status": "success"}, status=200)


class InvoiceInfoView(APIView):
    def get(self, request: Request, format=None):
        invoice_num = request.GET.get("invoice_num")
        invoice_instance = selectors.get_invoices_instance(invoice_num)
        serializer = OutputSerializers.InvoicesInfoSerializer(invoice_instance, many=False)
        return Response({"status": "success", "data": serializer.data}, status=HTTP_200_OK)


class ClientStatementEmailView(APIView):
    def post(self, request: Request, format=None):
        client_id = request.data.get("client_id")
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")

        if not all([client_id, start_date, end_date]):
            return Response({"status": "error", "message": "Missing required fields"}, status=400)

        from .Tasks.client_email_tasks import send_client_statement_email
        result = send_client_statement_email(client_id, start_date, end_date)
        
        status_code = 200 if result["status"] == "success" else 400
        return Response(result, status=status_code)
