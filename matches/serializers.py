from rest_framework import serializers
from matches.models import Match
class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ("id", "ride_request", "journey", "passenger", "created_at")
