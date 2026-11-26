from django.utils import timezone
from rest_framework import serializers
from journeys.models import Journey

MAX_SEATS = 65535


class JourneySerializer(serializers.ModelSerializer):
    driver_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Journey
        fields = ("id", "driver_id", "origin", "destination", "departure_time", "total_seats", "available_seats", "notes", "status", "created_at", "updated_at")
        read_only_fields = ("id", "driver_id", "available_seats", "status", "created_at", "updated_at")

    def validate_total_seats(self, value):
        if not 1 <= value <= MAX_SEATS:
            raise serializers.ValidationError("Seats must be between 1 and 65535.")
        return value

    def validate_departure_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("Departure time must be in the future.")
        return value

    def validate(self, attrs):
        origin = attrs.get("origin", getattr(self.instance, "origin", None))
        destination = attrs.get("destination", getattr(self.instance, "destination", None))
        if origin is not None and destination is not None:
            if origin.strip().casefold() == destination.strip().casefold():
                raise serializers.ValidationError({"destination": "Origin and destination must be different."})

        departure_time = attrs.get("departure_time", getattr(self.instance, "departure_time", None))
        if departure_time is not None and departure_time <= timezone.now():
            raise serializers.ValidationError({"departure_time": "Departure time must be in the future."})
        return attrs
