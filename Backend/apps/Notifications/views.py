from rest_framework.decorators import api_view
from .models import Notification
from .serializers import NotificationSerializer
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import status


@api_view(["GET"])
def Get_unreaded_notifications(request):
    Notifications = Notification.objects.filter(is_read=False)
    serializer_class = NotificationSerializer(Notifications, many=True)
    return Response(
        {"status": "success", "data": serializer_class.data}, status=status.HTTP_200_OK
    )


# @api_view(['POST'])
def send_notification_function(Title, message):
    data = {"title": Title, "message": message}
    serializer = NotificationSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
def mark_notification_as_read(request):
    notification_uuid = request.data.get("notification_uuid")
    try:
        # Retrieve the notification by UUID
        notification = Notification.objects.get(uuid=notification_uuid)
    except Notification.DoesNotExist:
        return Response(
            {"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Update the is_read field to True
    notification.is_read = True
    notification.save()

    return Response(
        {"message": "Notification marked as read"}, status=status.HTTP_200_OK
    )


@api_view(["PUT"])
def mark_all_notifications_as_read(request):
    Notification.objects.filter(is_read=False).update(is_read=True)

    return Response(
        {"message": "All notifications marked as read"}, status=status.HTTP_200_OK
    )
