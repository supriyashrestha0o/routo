
from rest_framework import serializers
from journeys.models import PassengerTravelPreference


class PassengerTravelPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassengerTravelPreference
        fields = (
            "id",
            "origin",
            "destination",
            "departure_time",
            "preference",
            "latitude",
            "longitude",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        origin = attrs.get("origin", getattr(self.instance, "origin", ""))
        destination = attrs.get(
            "destination",
            getattr(self.instance, "destination", ""),
        )

        if origin.strip().lower() == destination.strip().lower():
            raise serializers.ValidationError(
                "Pickup and destination cannot be the same."
            )

        return attrs
