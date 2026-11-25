from rest_framework import serializers
from routo.ride_requests.models import RideRequest

class RideRequestSerializer(serializers.ModelSerializer):
    passenger_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = RideRequest
        fields = ("id", "journey", "passenger_id", "seats_requested", "status", "created_at", "updated_at")
        read_only_fields = ("id", "passenger_id", "status", "created_at", "updated_at")
