from django.urls import path, include
from .views import rent_views, base_p_views

rent_urls = [
    path("info/", rent_views.RentProjectsApiView.as_view()),
    path("contracts/", rent_views.RentProjectContractsApiView.as_view()),
    path("ads/", rent_views.RentProjectAdsApiView.as_view()),
    path("guarantee-cheque/", rent_views.RentProjectGuaranteeChequesApiView.as_view()),
    path("operating-costs/", rent_views.RentProjectOperationgCost.as_view()),
    path("clear-insurance-tax/", rent_views.RentProjectInsuranceTaxApiView.as_view()),
]

selling_ind_urls = [
    # path("info/", rent_views.RentProjectsApiView.as_view()),
    # path("contracts/", rent_views.RentProjectContractsApiView.as_view()),
    # path("ads/", rent_views.RentProjectAdsApiView.as_view()),
    # path("guarantee-cheque/", rent_views.RentProjectGuaranteeChequesApiView.as_view()),
    # path("operating-costs/", rent_views.RentProjectOperationgCost.as_view()),
    # path("clear-insurance-tax/", rent_views.RentProjectInsuranceTaxApiView.as_view()),
]


urlpatterns = [
    path("", base_p_views.ProjectApiView.as_view()),
    path("contracts/", base_p_views.BaseProjectContractsApiView.as_view()),
    path("rent/", include(rent_urls)),
    path("selling_ind_p/", include(selling_ind_urls)),
]
