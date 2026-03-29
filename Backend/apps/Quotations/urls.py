from django.urls import path
from . import views

urlpatterns = [
    path("", views.QuotationsViewSet.as_view()),
    path("attachments/", views.QAttchmentsView.as_view()),
]
