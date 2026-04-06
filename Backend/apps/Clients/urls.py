from django.urls import path, include
from . import views

projcets_urls = [
    path("", views.ClientProjectAndCampaingsApiView.as_view()),
    path("payments/", views.InovicePaymentApiView.as_view()),
]


urlpatterns = [
    path("clients/", views.ClientsApiView.as_view()),
    path("info/", views.ClientInfoApiView.as_view()),
    path("projects/", include(projcets_urls)),
    path("email-statement/", views.SendFinancialReportEmailApiView.as_view()),
    # path("invoice/", include(invoice_urls)),
]
