from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request


from .tasks import pagenator, log_tasks
from .db_queries import selectors
from .serializers import InputSerializers, ParamsSerializers


class MaterialApiView(APIView):
    def post(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(ParamsSerializers.AddNewMaterialSerializer, request.data)
        serializer = InputSerializers.MaterialSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=400)
        instance = serializer.save()

        tranaction = "تم أضافة خامة جديدة"
        username = request.data["username"]
        log_tasks.create_both_transaction_logs(instance, tranaction, username)

        return Response({"status": "success"}, status=HTTP_200_OK)

    def get(self, request: Request, format=None):
        materials = selectors.get_materials()

        pagenated_materials = pagenator.pagenator(materials, request)

        response_data = {"status": "success", "data": pagenated_materials}

        return Response(response_data, status=HTTP_200_OK)

    def delete(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(ParamsSerializers.MatrerialNameSerializer, request.data)
        material_instance = selectors.get_specific_material_instance(request.data["material_name"])
        material_instance.delete()

        tranaction = "تم حذف خامة من المخزن"
        username = request.data["username"]
        log_tasks.create_both_transaction_logs(material_instance, tranaction, username)

        return Response({"status": "success"}, status=HTTP_200_OK)

    def patch(self, request: Request, format=None):
        material_instance = selectors.get_specific_material_instance(request.data["old_material_name"])
        serializer = InputSerializers.UpdateMaterialSerializer(instance=material_instance, data=request.data)
        if not serializer.is_valid():
            return Response({"status": "faild", "errors": serializer.errors}, status=400)
        instance = serializer.save()

        tranaction = "تم تعديل خامة من المخزن"
        username = request.data["username"]
        log_tasks.create_both_transaction_logs(instance, tranaction, username, instance.quantity_in_unit)

        return Response({"status": "success"}, status=HTTP_200_OK)


class FilterMaterialsAPiView(APIView):
    def get(self, request: Request, format=None):
        material_name = request.GET.get("material_name", "None")
        materials = selectors.filter_by_name(material_name)
        pagenated_materials = pagenator.pagenator(materials, request)
        response_data = {"status": "success", "data": pagenated_materials}
        return Response(response_data, status=HTTP_200_OK)


class MaterialsNamesApiView(APIView):
    def get(self, request: Request, format=None):
        materials = selectors.get_materials_names()
        response_data = {"status": "success", "data": materials}
        return Response(response_data, status=HTTP_200_OK)


class MaterialQuantityApiView(APIView):

    def post(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(ParamsSerializers.MatrerialNameSerializer, request.data)
        material_name = request.data.get("material_name")
        material_instance = selectors.get_specific_material_instance(material_name)

        added_quantity = request.data["quantity"]
        old_quantity = material_instance.quantity_in_kilo
        material_instance.quantity_in_kilo = material_instance.quantity_in_kilo + int(added_quantity)
        material_instance.save()

        driver_name = request.data.get("driver_name", "None")
        carplate_number = request.data.get("car_plate_number", "None")
        user_name = request.data["username"]
        log_tasks.create_both_transaction_logs(
            material_instance,
            f"اضافة كميه {added_quantity} للخامه {material_instance.material_name}",
            user_name,
            old_quantity,
            driver_name,
            carplate_number,
        )

        response_data = {"status": "success"}
        return Response(response_data, status=HTTP_200_OK)


class FillMaterialsView(APIView):
    def patch(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(ParamsSerializers.FillMatrerialSerializer, request.data)
        source_material_instance = selectors.get_specific_material_instance(
            request.data["source_material_name"]
        )
        target_material_instance = selectors.get_specific_material_instance(
            request.data["target_material_name"]
        )
        source_quantity = request.data["source_qty"]
        target_added_qty = request.data["target_added_qty"]

        target_material_instance.quantity_in_unit += float(target_added_qty)
        target_material_instance.save()

        source_material_instance.quantity_in_unit -= float(source_quantity)
        source_material_instance.save()

        return Response({"status": "success"}, status=HTTP_200_OK)
