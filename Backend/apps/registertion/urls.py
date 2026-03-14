from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r"users", views.SignUPViewSet, basename="users")

url_Auth = [
    path("", include(router.urls)),
    path("user/confirm-email/", views.SignUPViewSet.as_view({"post": "confirm_email"})),
    path("user/resend-otp/", views.SignUPViewSet.as_view({"post": "send_reset_otp"})),
    path("user/login/", views.LoginView.as_view()),
    path("user/logout/", views.APILogoutView.as_view()),
    path("refresh-Token/", TokenRefreshView.as_view()),
    path("update_user_type/", views.update_user_type),
    path("user/login/", views.LoginView.as_view()),
    path("is_password_correct/", views.is_password_correct),
    path("user/verify-otp/", views.VerifyOTPView.as_view(), name="verify_otp"),
]

url_Password = [
    path("forgot_password/", views.ForgetPasswordView.as_view()),
    path("reset_password/<str:token>", views.reset_password),
]

urlpatterns = (
    [
        path("", include(router.urls)),
    ]
    + url_Auth  # noqa
    + url_Password  # noqa
)
