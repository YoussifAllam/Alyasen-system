from django.urls import path
from . import views

urlpatterns = [
    path("clients/", views.ClientsApiView.as_view()),
    path("info/", views.ClientInfoApiView.as_view()),
    # path("email-statement/", views.ClientStatementEmailView.as_view()),
    # path("invoice/", include(invoice_urls)),
]
