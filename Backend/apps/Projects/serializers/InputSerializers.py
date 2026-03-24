from rest_framework import serializers
from .. import models


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BaseProject
        fields = ['name', 'project_type', 'project_status', 'supplier']
