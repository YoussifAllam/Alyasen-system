from django.urls import path
from . import views

urlpatterns = [
    path("projects/", views.ProjectApiView.as_view()),
]
