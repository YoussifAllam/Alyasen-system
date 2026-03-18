from django.urls import path
from . import views

urlpatterns = [
    path("get-unreaded-notifications/", views.Get_unreaded_notifications),
    path("mark-notification-as-read/", views.mark_notification_as_read),
    path("mark-all-notifications-as-read/", views.mark_all_notifications_as_read),
]
