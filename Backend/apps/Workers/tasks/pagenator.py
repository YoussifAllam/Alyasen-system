from rest_framework.pagination import PageNumberPagination


def pagenator(queryset, request, serializer_class, page_size=20, **serializer_kwargs):
    paginator = PageNumberPagination()
    paginator.page_size = page_size
    paginated_objects = paginator.paginate_queryset(queryset, request)

    # Default serializer context
    default_context = {"request": request}
    if "context" in serializer_kwargs:
        serializer_kwargs["context"].update(default_context)
    else:
        serializer_kwargs["context"] = default_context

    serializer = serializer_class(paginated_objects, many=True, **serializer_kwargs)
    paginated_response = paginator.get_paginated_response(serializer.data)

    response_data = {
        "count": paginated_response.data["count"],
        "next": paginated_response.data["next"],
        "previous": paginated_response.data["previous"],
        "results": paginated_response.data["results"],
    }
    return response_data
