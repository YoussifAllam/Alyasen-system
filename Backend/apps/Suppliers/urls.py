from django.urls import path, include
from . import views


urlpatterns = [
    path("suppliers/", views.SupplierApiView.as_view()),
    path("info/", views.SupplierInfoApiView.as_view()),
    path("payment/", views.InovicePaymentApiView.as_view()),
]
