from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_201_CREATED
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from .tasks.pagenator import pagenator
from .db_queries import selectors, services
from .serializers import OutputSerializers, ParamsSerializers, InputSerializers


class MixturesApiView(APIView):
    def get(self, request: Request, format=None):
        name = request.GET.get("name", "")
        filtred_transactions = selectors.get_mixtures(name)
        response_data = pagenator(filtred_transactions, request, OutputSerializers.MixturesSerializer)
        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(ParamsSerializers.MixtureNameSerializer, request.data)
        name = request.data.get("name")
        services.create_mixture_instance(name)
        return Response({"status": "success"}, status=HTTP_201_CREATED)

    def patch(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(ParamsSerializers.MixtureNameSerializer, request.data)
        mixture_instance = selectors.get_specific_mixture_instance(request.data["id"])
        name = request.data.get("name")
        services.update_mixture_instance_name(mixture_instance, name)
        return Response({"status": "success"}, status=HTTP_200_OK)

    def delete(self, request: Request, format=None):
        mixture_instance = selectors.get_specific_mixture_instance(request.data["id"])
        mixture_instance.delete()
        return Response({"status": "success"}, status=HTTP_204_NO_CONTENT)


class MixtureMaterialsApiView(APIView):
    def get(self, request: Request, format=None):
        mixture_id = request.GET.get("mixture_id")
        mixture_materials = selectors.get_mixture_materials(mixture_id)
        response_data = pagenator(mixture_materials, request, OutputSerializers.MixtureMaterialsSerializer)
        return Response(response_data, status=HTTP_200_OK)

    def post(self, request: Request, format=None):
        print("/n ------------------", request.data)
        mixture_instance = selectors.get_specific_mixture_instance(request.data["mixture_id"])
        material_instance = selectors.get_specific_material_instance(request.data["material_name"])

        if selectors.check_if_matrial_in_mixture(mixture_instance, material_instance):
            return Response({"حطأ": "لقد تم استخدام هذا الخامة في هذه الخلطة من قبل"}, status=400)

        input_serializer = InputSerializers.MixtureMaterialsSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response({"status": "faild", "errors": input_serializer.errors}, status=400)

        instance = input_serializer.save(mixture_fk=mixture_instance, material_fk=material_instance)

        output_serializer = OutputSerializers.MixtureMaterialsSerializer(instance)
        return Response(
            {"status": "success", "data": output_serializer.data},
            status=HTTP_201_CREATED,
        )

    def delete(self, request: Request, format=None):

        mixture_material_instance = selectors.get_specific_mixture_material_instance(request.data["id"])
        mixture_material_instance.delete()

        return Response(
            {"status": "success"},
            status=HTTP_204_NO_CONTENT,
        )


class MixtureInfoApiView(APIView):
    def get(self, request: Request, format=None):
        mixture_id = request.GET.get("mixture_id")
        mixture_instance = selectors.get_specific_mixture_instance(mixture_id)
        serializer = OutputSerializers.MixtureInfoSerializer(mixture_instance)
        return Response({"status": "success", "data": serializer.data}, status=HTTP_200_OK)

    def patch(self, request: Request, format=None):
        ParamsSerializers.validate_serializer(ParamsSerializers.UpdateMixtureInfo, request.data)

        mixture_instance = selectors.get_specific_mixture_instance(request.data["mixture_id"])

        new_profit = float(request.data["profit"])
        new_manufacturing_cost = float(request.data["manufacturing_cost"])

        mixture_instance.profit = new_profit
        mixture_instance.manufacturing_cost = new_manufacturing_cost
        mixture_instance.save()

        return Response({"status": "success"}, status=HTTP_200_OK)
