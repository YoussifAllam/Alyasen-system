from os import name
from apps.Users.models import User


def Create_user(validated_data: dict) -> User:
    user = User.objects.create_user(
        username=validated_data["email"],
        name=validated_data["name"],
        email=validated_data["email"],
        user_type=validated_data["user_type"],
        first_name=(validated_data.get("name") if validated_data.get("name") else ""),
    )
    if validated_data.get("password"):
        user.set_password(validated_data["password"])
        user.save()
    return user
