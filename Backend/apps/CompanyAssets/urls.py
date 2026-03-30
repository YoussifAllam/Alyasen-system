from django.urls import path
from . import views

urlpatterns = [
    path("", views.CompanyAssetsView.as_view()),
    path("attachments/", views.CompanyAssetsAttachmentsApiView.as_view()),
]
