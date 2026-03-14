from django.urls import path
from . import views

urlpatterns = [
    path("materials/", views.MaterialApiView.as_view()),
    path("materials-names/", views.MaterialsNamesApiView.as_view()),
    path("filter/", views.FilterMaterialsAPiView.as_view()),
    path("material-quantity/", views.MaterialQuantityApiView.as_view()),
    path("fill-materials/", views.FillMaterialsView.as_view()),
]
