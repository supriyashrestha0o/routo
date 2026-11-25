from rest_framework import serializers
from routo.journeys.models import Journey

class JourneySerializer(serializers.ModelSerializer):
    driver_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Journey
        fields = ("id", "driver_id", "origin", "destination", "departure_time", "total_seats", "available_seats", "notes", "status", "created_at", "updated_at")
        read_only_fields = ("id", "driver_id", "available_seats", "status", "created_at", "updated_at")
    def validate_total_seats(self, value):
        if value < 1:
            raise serializers.ValidationError("At least one seat is required.")
        return value
