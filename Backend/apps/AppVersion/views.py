from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.permissions import AllowAny

from .models import AppVersion


class VersionCheckApiView(APIView):
    """
    Public endpoint to check the latest app version.
    No authentication required since the app checks before login.
    Returns: {"version": "V1.0.1", "url": "https://.../setup.exe", "notes": "..."}
    """

    permission_classes = [AllowAny]

    def get(self, request, format=None):
        app_version = AppVersion.objects.first()

        if app_version and app_version.setup_file:
            file_url = request.build_absolute_uri(app_version.setup_file.url)
            return Response(
                {
                    "version": app_version.version,
                    "url": file_url,
                    "notes": app_version.notes,
                },
                status=HTTP_200_OK,
            )

        return Response(
            {"version": None, "url": None, "notes": ""},
            status=HTTP_200_OK,
        )
