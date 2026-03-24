from rest_framework import serializers
from .. import models
from apps.Suppliers.serializers.OutputSerializers import SupplierSerializer


class ProjectContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProjectContracts
        fields = ['id', 'contract']


class ProjectSerializer(serializers.ModelSerializer):
    contracts = serializers.SerializerMethodField()
    supplier = SupplierSerializer(read_only=True)

    class Meta:
        model = models.BaseProject
        fields = ['id', 'name', 'project_type', 'project_status', 'supplier', 'created_date', 'contracts']

    def get_contracts(self, obj):
        contracts = models.ProjectContracts.objects.filter(project=obj)
        return ProjectContractSerializer(contracts, many=True, context=self.context).data
