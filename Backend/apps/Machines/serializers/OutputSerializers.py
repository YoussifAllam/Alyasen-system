from rest_framework import serializers
from ..models import Machines, MachineComponents, MachineRepairHistory


class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machines
        fields = "__all__"


class MachineComponentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = MachineComponents
        fields = ["id", "name"]


class MachineInfoSerializer(serializers.ModelSerializer):
    last_repair_date = serializers.SerializerMethodField()
    status = serializers.CharField(default="تعمل")

    class Meta:
        model = Machines
        fields = ["id", "image", "name", "status", "last_repair_date"]

    def get_last_repair_date(self, obj: Machines):
        date = obj.last_repair_date
        if date:
            return date.strftime("%Y-%m-%d")
        return "لا يوجد تاريخ صيانه مسجل بعد"


class MachineRepairHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MachineRepairHistory
        exclude = ["machine"]
