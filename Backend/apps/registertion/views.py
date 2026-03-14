from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action, permission_classes, api_view
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import logout
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)
from rest_framework.request import Request
from django.shortcuts import get_object_or_404


from apps.registertion.db_queries.selectors import get_user_by_email
from apps.Users.models import UserTypeChoice

from .permissions import IsAdminOrPostOnly
from .serializers import InputSerializers
from .tasks import Auth_tasks, password_tasks
from .db_queries import selectors

User = get_user_model()


class SignUPViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = InputSerializers.SignUpSerializer
    permission_classes = [IsAdminOrPostOnly]
    lookup_field = "uuid"

    def create(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # tokens_data = Auth_tasks.send_otp_to_user_email(user)

            return Response(
                {
                    "user": serializer.data,
                    # "tokens": tokens_data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def confirm_email(self, request):
        Response_data, Response_status = Auth_tasks.confirm_email_using_otp(request)
        return Response(Response_data, status=Response_status)

    @action(detail=False, methods=["post"])
    def send_reset_otp(self, request):
        Response_data, Response_status = Auth_tasks.send_reset_otp(request)
        return Response(Response_data, status=Response_status)


class ForgetPasswordView(APIView):
    def post(self, request: Request) -> Response:
        Response_data, Response_status = password_tasks.send_rest_password_otp(request)
        return Response(Response_data, status=Response_status)


@api_view(["POST"])
def reset_password(request: Request, token: str) -> Response:
    Response_data, Response_status = password_tasks.reset_password(request, token)
    return Response(Response_data, status=Response_status)


class LoginView(APIView):
    def post(self, request: Request) -> Response:
        email = request.data.get("email")
        password = request.data.get("password")  # Required only for investors

        if not email or not password:
            return Response({"message": " يرجي أدخال الأيميل و كلمة المرور"}, status=400)

        user = selectors.get_user_by_email(email)

        if not password or not user.check_password(password):
            return Response(
                {"error": "كلمة المرور غير صحيح"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_approvid:
            return Response(
                {"error": "برجاء الأنتظار حتى يتم الموافقة على حسابك"},
                status=400,
            )

        return Response(
            {"status": "success", "name": user.name},
            status=200,
        )


class VerifyOTPView(APIView):
    def post(self, request: Request) -> Response:
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response(
                {"message": "Email and OTP are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email=email).first()

        if not user:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if user.user_type == UserTypeChoice.INVESTOR:
            return Response(
                {"message": "Investors must log in using a password."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not (user.otp == int(otp) and Auth_tasks.is_otp_valid(user.otp_created_at)):
            return Response(
                {"message": "Invalid or expired OTP"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.email_verified = True
        user.otp = 0
        user.save()

        tokens = Auth_tasks.generate_token_for_user(user)

        return Response(
            {
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class APILogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        if self.request.data.get("all"):
            token: OutstandingToken
            for token in OutstandingToken.objects.filter(user=request.user):
                _, _ = BlacklistedToken.objects.get_or_create(token=token)
            return Response({"status": "OK, goodbye, all refresh tokens blacklisted"})
        refresh_token = self.request.data.get("refresh_token")
        token = RefreshToken(token=refresh_token)
        token.blacklist()
        logout(request)
        return Response({"status": "OK, goodbye"})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user_type(request):
    Response_data, Response_status = Auth_tasks.choose_user_type(request)
    return Response(Response_data, status=Response_status)


@api_view(["Post"])
@permission_classes([IsAuthenticated])
def is_password_correct(request: Request):
    user = request.user
    if user.check_password(request.data.get("password", " ")):
        return Response({"status": "success"}, status.HTTP_200_OK)
    else:
        return Response({"status": "faild"}, status.HTTP_400_BAD_REQUEST)
