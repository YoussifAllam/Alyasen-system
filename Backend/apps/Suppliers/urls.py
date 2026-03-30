from django.urls import path, include
from . import views

projects_urls = [
    path("", views.SupplierProjectsApiView.as_view()),
]

urlpatterns = [
    path("suppliers/", views.SupplierApiView.as_view()),
    path("info/", views.SupplierInfoApiView.as_view()),
    path("payment/", views.InovicePaymentApiView.as_view()),
    path("projects/", include(projects_urls)),
]
