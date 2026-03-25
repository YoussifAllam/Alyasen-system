from django.urls import path
from . import views

urlpatterns = [
    path("", views.ProjectApiView.as_view()),
]
