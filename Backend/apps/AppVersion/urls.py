from django.urls import path
from . import views

urlpatterns = [
    path("version-check/", views.VersionCheckApiView.as_view()),
]
