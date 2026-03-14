from django.urls import path
from . import views

urlpatterns = [
    path("Warehouse-Transactions/", views.WarehouseTransactionViewSet.as_view()),
    path("Warehouse-today-Transactions/", views.WarehouseTodayTransactionApiView.as_view()),
]
