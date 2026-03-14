from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # First, get the standard error response from DRF
    response = exception_handler(exc, context)

    # Now, reformat the response data if the 'detail' key exists
    # This is the key DRF uses for errors like NotFound, PermissionDenied, etc.
    if response is not None and "detail" in response.data:
        response.data = {"error": response.data["detail"]}

    return response
