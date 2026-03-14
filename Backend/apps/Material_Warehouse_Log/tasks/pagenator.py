from rest_framework.pagination import PageNumberPagination
from ..serializers.OutputSerializers import WarehouseTransactionsLogSerializer


def pagenator(Target_products, request):
    paginator = PageNumberPagination()
    paginator.page_size = 20
    paginated_objects = paginator.paginate_queryset(Target_products, request)

    serializer = WarehouseTransactionsLogSerializer(
        paginated_objects, many=True, context={"request": request}
    )

    paginated_response = paginator.get_paginated_response(serializer.data)

    # Add custom status field to the response data
    paginated_response.data["status"] = "success"

    # return paginated_response
    response_data = {
        "status": "success",
        "data": {
            "count": paginated_response.data["count"],
            "next": paginated_response.data["next"],
            "previous": paginated_response.data["previous"],
            "results": paginated_response.data["results"],
        },
    }
    return response_data
