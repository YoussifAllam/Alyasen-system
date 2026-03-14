from django.urls import path
from . import views

urlpatterns = [
    path("daily-report/", views.DailyReportApiView.as_view(), name="daily-report"),
    path("month-report/", views.MonthReportApiView.as_view(), name="month-report"),
    path("year-report/", views.YearReportApiView.as_view(), name="year-report"),
]
