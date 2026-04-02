from rest_framework import serializers
from ..models import Campaine


class CampaineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaine
        fields = "__all__"
