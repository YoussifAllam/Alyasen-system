from django.urls import path, include
from . import views

invoice_urls = [
    path("invoices/", views.SupplierInovicesApiView.as_view()),
    path("payment/", views.InovicePaymentApiView.as_view()),
    path("materials/", views.InvoiceMaterialsApiView.as_view()),
    path(
        "move-to-warehouse/",
        views.MoveInvoiceMaterialsToWarehouseAPIView.as_view(),
    ),
    path("info/", views.InvoiceInfoView.as_view()),
]

urlpatterns = [
    path("suppliers/", views.SupplierApiView.as_view()),
    path("info/", views.SupplierInfoApiView.as_view()),
    path("invoice/", include(invoice_urls)),
]
