from rest_framework import serializers
from notifications.models import DeviceToken

class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ("id", "token", "platform", "active", "created_at")
        read_only_fields = ("id", "active", "created_at")
        extra_kwargs = {
            # Registration is an idempotent upsert. The view handles the
            # database-level uniqueness constraint.
            "token": {"validators": []},
        }
