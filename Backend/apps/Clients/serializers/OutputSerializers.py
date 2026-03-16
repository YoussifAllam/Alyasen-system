from rest_framework import serializers
from ..models import Client


class ClientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"

# class ClientPaymentsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = InvoicePayment
#         exclude = ["id", "client_fk"]

class ClientInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = (
            "name",
            "phone",
            "email",
        )


