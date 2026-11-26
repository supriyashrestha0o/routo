from rest_framework import serializers
from journeys.models import Journey
from matches.models import Match
from reviews.models import Review
from ride_requests.models import RideRequest


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Review
        fields = ("id", "reviewer_id", "reviewed_user", "journey", "rating", "comment", "created_at")
        read_only_fields = ("id", "created_at")
        extra_kwargs = {"journey": {"required": True, "allow_null": False}}

    @staticmethod
    def _is_accepted_passenger(journey, passenger):
        return Match.objects.filter(
            journey=journey,
            passenger=passenger,
            ride_request__journey=journey,
            ride_request__passenger=passenger,
            ride_request__status=RideRequest.Status.ACCEPTED,
        ).exists()

    def validate(self, attrs):
        request = self.context.get("request")
        if request is None:
            return attrs

        reviewer = request.user
        reviewed_user = attrs.get("reviewed_user")
        journey = attrs.get("journey")
        if reviewed_user is None or journey is None:
            return attrs

        if reviewer.pk == reviewed_user.pk:
            raise serializers.ValidationError({"reviewed_user": "You cannot review yourself."})
        if journey.status != Journey.Status.COMPLETED:
            raise serializers.ValidationError({"journey": "Reviews can only be created for completed journeys."})

        if reviewer.pk == journey.driver_id:
            if not self._is_accepted_passenger(journey, reviewed_user):
                raise serializers.ValidationError({"reviewed_user": "You can only review an accepted passenger on this journey."})
        elif self._is_accepted_passenger(journey, reviewer):
            if reviewed_user.pk != journey.driver_id:
                raise serializers.ValidationError({"reviewed_user": "Passengers can only review the journey driver."})
        else:
            raise serializers.ValidationError({"journey": "You must be the driver or an accepted passenger for this journey."})

        if Review.objects.filter(reviewer=reviewer, reviewed_user=reviewed_user, journey=journey).exists():
            raise serializers.ValidationError({"journey": "You have already reviewed this user for this journey."})
        return attrs
