from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_201_CREATED
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .Tasks.pagenator import pagenator
from .db_queries import selectors, services
from .serializers import InputSerializers, OutputSerializers
from .Tasks import materials_tasks

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log


class SegmentalInovicesApiView(APIView):
    def get(self, request: Request, format=None):
        invoices_instances = selectors.get_invoice_instances()
        response_data = pagenator(invoices_instances, request, OutputSerializers.InvoiceSerializer, 13)
        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        serializer = InputSerializers.InvoicesSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=400)
        invoice_instance = serializer.save()

        tranaction = f"تم اضافة فاتورة قطاعي رقم {invoice_instance.invoice_number}"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response(
            {"status": "success", "data": {"invoice_number": invoice_instance.invoice_number}},
            status=HTTP_201_CREATED,
        )

    def delete(self, request: Request, format=None):
        invoice_num = request.data["invoice_num"]
        invoice_instance = selectors.get_specific_invoice_instance(invoice_num)
        invoice_instance.delete()

        tranaction = f"تم حذف فاتورة قطاعي رقم {invoice_instance.invoice_number}"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response({"status": "success"}, status=HTTP_204_NO_CONTENT)

    def patch(self, request: Request, format=None):
        invoice_num = request.data["invoice_num"]
        invoice_total_amount = request.data["invoice_total_amount"]
        invoice_instance = selectors.get_specific_invoice_instance(invoice_num)
        invoice_instance.invoice_total_amount = invoice_total_amount
        invoice_instance.save()
        return Response({"status": "success"}, status=200)


class InvoiceMaterialsApiView(APIView):
    def post(self, request: Request, format=None):
        invoice_num = request.data["invoice_num"]
        mixture_id = request.data["material_id"]
        req_qty_of_mixture = request.data["quantity_in_unit"]
        invoice_instance = selectors.get_specific_invoice_instance(invoice_num)
        material_instnace = selectors.get_specific_material_instance(mixture_id)

        if selectors.check_if_invoice_has_this_m(invoice_num, material_instnace):
            return Response({"خطأ": "هذا المنتج موجود بالفاتورة"}, status=400)

        status, message = materials_tasks.check_material_qty_availability(
            material_instnace, float(req_qty_of_mixture)
        )
        if not status:
            return Response({"خطأ": message}, status=400)

        serializer = InputSerializers.InvoiceMaterialsSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"خطا": serializer.errors}, status=400)

        serializer.save(invoice=invoice_instance, material=material_instnace)

        return Response({"status": "success"}, status=201)

    def delete(self, request: Request, format=None):
        material_id = request.data["material_id"]
        segmental_material_instance = selectors.get_specific_segmental_material_instance(material_id)
        segmental_material_instance.delete()

        return Response({"status": "success"}, status=HTTP_204_NO_CONTENT)

    def get(self, request: Request, format=None):
        invoice_num = request.GET.get("invoice_num")
        materials_instances = selectors.get_invoice_materials_instances(invoice_num)
        response_data = pagenator(materials_instances, request, OutputSerializers.InvoiceMaterialsSerializer)
        return Response({"status": "sucess", "data": response_data}, 200)


class MoveInvoiceMaterialsFromWarehouseAPIView(APIView):
    def post(self, request: Request):
        invoice_num = request.data["invoice_num"]

        invoice_instance = selectors.get_specific_invoice_instance(invoice_num)

        if invoice_instance.is_moved_to_warehouse:
            return Response({"خطأ": "هذه الفاتورة تم نقلها من المخزن من قبل"}, status=400)

        success, production_message = materials_tasks.create_material_production_from_invoice(
            invoice_instance
        )
        if not success:
            return Response({"خطأ": production_message}, status=400)
        invoice_instance.is_moved_to_warehouse = True
        invoice_instance.save()
        services.create_payment_record(invoice_instance.invoice_total_amount)
        return Response({"status": "success"}, status=200)


class InvoiceInfoApiview(APIView):
    def get(self, request: Request, format=None):
        invoice_num = request.GET.get("invoice_num")
        invoice_instance = selectors.get_specific_invoice_instance(invoice_num)
        serializer = OutputSerializers.InvoicesInfoSerializer(invoice_instance, many=False)
        return Response({"status": "success", "data": serializer.data}, status=HTTP_200_OK)


class PaymentView(APIView):
    def post(self, request: Request, format=None):
        amount = float(request.data["amount"])
        services.create_payment_record(amount)
        return Response({"status": "success"}, status=HTTP_200_OK)
