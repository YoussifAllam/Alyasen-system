from django.urls import path
from . import views

urlpatterns = [
    path("safe/", views.SafeView.as_view()),
    path("logs/", views.SafeLogsView.as_view()),
]
