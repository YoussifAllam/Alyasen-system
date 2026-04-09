from django.urls import path, include
from . import views

rent_urls = [
    path("info/", views.RentProjectsApiView.as_view()),
    path("contracts/", views.RentProjectContractsApiView.as_view()),
    path("ads/", views.RentProjectAdsApiView.as_view()),
    path("guarantee-cheque/", views.RentProjectGuaranteeChequesApiView.as_view()),
]

urlpatterns = [
    path("", views.ProjectApiView.as_view()),
    path("contracts/", views.BaseProjectContractsApiView.as_view()),
    path("rent/", include(rent_urls)),
]
