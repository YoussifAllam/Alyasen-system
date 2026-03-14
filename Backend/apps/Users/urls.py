from django.urls import path
from .views import (
    current_user,
    update_user,
)

urlpatterns = [
    path("userinfo/", current_user, name="user_info"),
    path("userinfo/update/", update_user, name="update_user"),
]
