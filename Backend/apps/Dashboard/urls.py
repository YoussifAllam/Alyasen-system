from django.urls import path
from . import views

urlpatterns = [
    path("expenses-graph-data/", views.ExpensesGraphApiView.as_view()),
    path("top-lists-data/", views.TopListsDataApiView.as_view()),
    # path("inventory-level/", views.InventoryMaterialsLevelApiView.as_view()),
    # path("performance-graph/", views.PerformanceGraphApiView.as_view()),
    path("users-status/", views.UsersStutsApiView.as_view()),
    path("users/", views.UsersApiView.as_view()),
    path("upcoming-insurance-tax-data/", views.UpcomingInsuranceTaxApiView.as_view()),
    path("guarantee-checks/", views.GuaranteeChecksApiView.as_view()),
    path("database-backup/", views.DatabaseBackupApiView.as_view()),
]
