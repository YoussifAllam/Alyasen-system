from django.urls import path
from . import views

urlpatterns = [
    path("", views.CampaineListCreateView.as_view()),
]
