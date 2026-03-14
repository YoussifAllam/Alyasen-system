from django.urls import path, include
from . import views

invoice_urls = [
    path("invoices/", views.ClientInovicesApiView.as_view()),
    path("payment/", views.ClientPaymentsApiView.as_view()),
    path("mixtures/", views.InvoiceMaterialsApiView.as_view()),
    path(
        "move-from-warehouse/",
        views.MoveInvoiceMaterialsFromWarehouseAPIView.as_view(),
    ),
    path("info/", views.InvoiceInfoView.as_view()),
]

urlpatterns = [
    path("clients/", views.ClientsApiView.as_view()),
    path("info/", views.ClientInfoApiView.as_view()),
    path("email-statement/", views.ClientStatementEmailView.as_view()),
    path("invoice/", include(invoice_urls)),
]
