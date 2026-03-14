from rest_framework.serializers import ModelSerializer

from apps.Users.models import User


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "uuid",
            "name",
            "email",
            "created_Date",
            "user_type",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get("user_type") == "Admin":
            data["user_type"] = "أدمن"
            return data
        data["user_type"] = "محاسب"

        return data
