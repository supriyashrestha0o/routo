from rest_framework import serializers
from ride_requests.models import RideRequest

MAX_SEATS = 65535


class RideRequestSerializer(serializers.ModelSerializer):
    passenger_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = RideRequest
        fields = ("id", "journey", "passenger_id", "seats_requested", "status", "created_at", "updated_at")
        read_only_fields = ("id", "passenger_id", "status", "created_at", "updated_at")

    def validate_seats_requested(self, value):
        if not 1 <= value <= MAX_SEATS:
            raise serializers.ValidationError("Seats requested must be between 1 and 65535.")
        return value
