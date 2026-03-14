from django.urls import path
from . import views

urlpatterns = [
    path("expenses/", views.ExpensesApiView.as_view()),
    path("expenses_summery/", views.ExpensesSummeryApiView.as_view()),
]
