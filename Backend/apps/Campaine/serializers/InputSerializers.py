from rest_framework import serializers

class CreateCampaineItemSerializer(serializers.Serializer):
    supplier_id = serializers.IntegerField()
    project_id = serializers.IntegerField()
    amount = serializers.FloatField()

class CreateCampaineSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    client_id = serializers.IntegerField()
    items = CreateCampaineItemSerializer(many=True)
