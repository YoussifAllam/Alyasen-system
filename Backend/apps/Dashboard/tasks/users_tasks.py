from apps.Users.models import User
from django.db.models import Count, Q


def get_users_status():
    users = User.objects.only("id", "is_approvid").aggregate(
        approved_count=Count("is_approvid", filter=Q(is_approvid=True)),
        unapproved_count=Count("is_approvid", filter=Q(is_approvid=False)),
    )

    return {
        "approved_count": users["approved_count"],
        "unapproved_count": users["unapproved_count"],
    }


def get_users(is_approvid: bool) -> User:
    users = User.objects.only("uuid", "name", "created_Date", "is_approvid", "user_type").filter(
        is_approvid=is_approvid
    )
    return users
