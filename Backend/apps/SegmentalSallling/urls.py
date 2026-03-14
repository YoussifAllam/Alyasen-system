from django.urls import path, include
from . import views

invoice_urls = [
    path("invoices/", views.SegmentalInovicesApiView.as_view()),
    path("materials/", views.InvoiceMaterialsApiView.as_view()),
    path(
        "move-from-warehouse/",
        views.MoveInvoiceMaterialsFromWarehouseAPIView.as_view(),
    ),
    path("info/", views.InvoiceInfoApiview.as_view()),
]

urlpatterns = [
    path("invoice/", include(invoice_urls)),
    path("SegmentalPayment/", views.PaymentView.as_view()),
]
