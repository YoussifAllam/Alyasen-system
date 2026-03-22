from django.urls import path
from . import views

urlpatterns = [
    path("company-assets/", views.CompanyAssetsView.as_view()),
]
