from django.urls import path
from . import views

urlpatterns = [
    path("workers/", views.WorkersView.as_view()),
    path("info/", views.WorkerInfoView.as_view()),
    path("absence/", views.WorkerAbsenceView.as_view()),
    path("deduction/", views.DeductionsView.as_view()),
    path("advance/", views.WorkerAdvanceView.as_view()),
    path("attendance/", views.WorkerAttendanceView.as_view()),
    path("finish-shift/", views.FinishWorkerShiftView.as_view()),
    path("alternative/", views.WorkerAlternativesView.as_view()),
    path("salary-report/", views.WorkerSalaryReport.as_view()),
]
