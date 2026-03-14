from django.urls import path
from . import views

urlpatterns = [
    path("machine/", views.MachineView.as_view()),
    path("machine-components/", views.MachineComponentsView.as_view()),
    path("info/", views.MachineInfo.as_view()),
    path("repair-history/", views.MachineRepairHistoryView.as_view()),
]
