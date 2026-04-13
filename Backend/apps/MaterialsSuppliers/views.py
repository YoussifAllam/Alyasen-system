from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from django.db import transaction

from .tasks.pagenator import pagenator
from .db_queries import selectors, services
from .serializers import InputSerializers, OutputSerializers, ParamsSerializers
from .tasks import celery_tasks

from apps.TransactionsLog.tasks.celery_tasks import create_transaction_log
from apps.Safe.tasks.celery_tasks import reduce_safe_balance


class SupplierApiView(APIView):
    def get(self, request: Request, format=None):
        filtred_transactions = selectors.get_suppliers(request)

        response_data = pagenator(
            filtred_transactions, request, OutputSerializers.SupplierSerializer
        )

        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        serializer = InputSerializers.SupplierSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "faild", "errors": serializer.errors}, status=400
            )
        serializer.save()

        tranaction = "تم أضافة مورد جديد للنظام"
        username = request.data["username"]
        create_transaction_log(transaction_data=tranaction, username=username)

        return Response({"status": "success"}, status=HTTP_200_OK)


class SupplierInfoApiView(APIView):
    def get(self, request: Request, format=None):
        supplier_id = request.GET.get("id")
        supplier_instance = selectors.get_supplier_instance(supplier_id)
        serializer = OutputSerializers.SupplierSerializer(
            supplier_instance, many=False, context={"request": request}
        )
        return Response({"status": "succes", "data": serializer.data}, 200)


class InovicePaymentApiView(APIView):
    def post(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(
            ParamsSerializers.InvoicePaymentSerializer, data=request.data
        )
        supplier_id = request.data["supplier_id"]
        payment_amount = float(request.data["payment_amount"])
        notes = request.data.get("notes", "None")
        username = request.data["username"]

        supplier_instance = selectors.get_supplier_instance(supplier_id)

        if payment_amount > supplier_instance.total_amount_payable:
            return Response({"حطأ": "المبلغ المدفوع اكبر من المتبقي "}, 400)

        services.pay_for_supplier(supplier_instance, payment_amount)

        celery_tasks.create_material_supplier_payment_record.delay(
            supplier_id, payment_amount, notes
        )
        reduce_safe_balance.delay(
            payment_amount, f"تم دفع دفعه للمقاول {supplier_instance.name}", username
        )
        create_transaction_log.delay(
            username=username,
            transaction_data=f"تم تسديد دفعه للمورد {supplier_instance.name} بمبلغ {payment_amount}",
        )

        return Response({"status": "sucess"}, 200)

    def get(Self, request: Request, format=None):
        supplier_id = request.GET.get("supplier_id")
        payments_instances = selectors.get_supplier_payments_instances(supplier_id)

        response_data = pagenator(
            payments_instances, request, OutputSerializers.InvoicePaymentsSerializer
        )
        return Response({"status": "sucess", "data": response_data}, 200)


class SupplierInovicesApiView(APIView):
    def get(self, request: Request, format=None):
        supplier_id = request.GET.get("supplier_id")
        invoices_instances = selectors.get_supplier_invoices_instance(supplier_id)
        response_data = pagenator(
            invoices_instances, request, OutputSerializers.InvocesSerializer, 13
        )
        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        supplier_id = request.data["supplier_id"]
        supplier_instance = selectors.get_supplier_instance(supplier_id)
        serializer = InputSerializers.InvoicesSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"status": "faild", "errors": serializer.errors}, status=400
            )
        invoice_instance = serializer.save(supplier=supplier_instance)

        tranaction = f"تم اضافة فاتورة رقم {invoice_instance.invoice_number} للمورد {supplier_instance.name}"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response(
            {"status": "success", "invoice_number": invoice_instance.invoice_number},
            status=HTTP_200_OK,
        )

    def delete(self, request: Request, format=None):
        invoice_num = request.data["invoice_num"]
        invoice_instance = selectors.get_invoices_instance(invoice_num)
        invoice_instance.delete()

        tranaction = f"تم حذف فاتورة رقم {invoice_instance.invoice_number} من المورد {invoice_instance.supplier.name}"
        username = request.data["username"]
        create_transaction_log.delay(transaction_data=tranaction, username=username)

        return Response({"status": "success"}, status=HTTP_204_NO_CONTENT)


class InvoiceMaterialsApiView(APIView):
    def post(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(
            ParamsSerializers.inviceMaterialsPSerializer, data=request.data
        )

        invoice_num = request.data["invoice_num"]
        invoice_instance = selectors.get_invoices_instance(invoice_num)
        serializer = InputSerializers.InvoiceMaterials(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"status": "faild", "errors": serializer.errors}, status=400
            )

        serializer.save(invoice=invoice_instance)

        return Response({"status": "success", "data": serializer.data}, status=201)

    def delete(self, request: Request, format=None):
        material_id = request.data["material_id"]
        material_instance = selectors.get_specific_invoice_materials_instance(
            material_id
        )
        material_instance.delete()

        return Response(
            {"status": "success"},
            status=HTTP_204_NO_CONTENT,
        )

    def get(self, request: Request, format=None):
        invoice_num = request.GET.get("invoice_num")
        materials_instances = selectors.get_invoice_materials_instance(invoice_num)

        response_data = pagenator(
            materials_instances, request, OutputSerializers.InvoiceMaterialsSerializer
        )
        return Response({"status": "sucess", "data": response_data}, 200)


class InvoiceInfoView(APIView):
    def get(self, request: Request, format=None):
        invoice_num = request.GET.get("invoice_num")
        invoice_instance = selectors.get_invoices_instance(invoice_num)
        serializer = OutputSerializers.InvoicesInfoSerializer(
            invoice_instance, many=False
        )
        return Response(
            {"status": "success", "data": serializer.data}, status=HTTP_200_OK
        )

    def patch(self, request: Request, format=None):

        invoice_num = request.data["invoice_num"]
        invoice_total_amount = request.data["invoice_total_amount"]
        paid_amount = request.data["paid_amount"]

        invoice_instance = selectors.get_invoices_instance(invoice_num)

        invoice_instance.invoice_total_amount = invoice_total_amount
        invoice_instance.save()

        services.update_supplier_balance(
            float(invoice_total_amount), float(paid_amount), invoice_instance.supplier
        )

        return Response({"status": "success"}, status=HTTP_200_OK)
