from ..models import Mixtures, MixtureMaterial
from rest_framework import serializers


class MixturesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mixtures
        fields = "__all__"


class MixtureMaterialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MixtureMaterial
        fields = "__all__"
        extra_kwargs = {"mixture_fk": {"required": False}, "material_fk": {"required": False}}
