from django.urls import path
from . import views

urlpatterns = [
    path("mixtures/", views.MixturesApiView.as_view()),
    path("materials/", views.MixtureMaterialsApiView.as_view()),
    path("mixture_info/", views.MixtureInfoApiView.as_view()),
]
