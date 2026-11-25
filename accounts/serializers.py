from rest_framework import serializers
from accounts.models import RouteUser

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteUser
        fields = ("id", "firebase_uid", "email", "created_at")
        read_only_fields = fields
