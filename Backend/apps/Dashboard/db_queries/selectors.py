from apps.Users.models import User

from rest_framework.exceptions import NotFound


def get_user_instance(user_uuid):
    try:
        return User.objects.get(uuid=user_uuid)
    except User.DoesNotExist:
        raise NotFound({"الخطاء": "لا يوجد مستخدم بهذا الكود"})
