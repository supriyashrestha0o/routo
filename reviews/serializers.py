from rest_framework import serializers
from reviews.models import Review
class ReviewSerializer(serializers.ModelSerializer):
    reviewer_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Review
        fields = ("id", "reviewer_id", "reviewed_user", "journey", "rating", "comment", "created_at")
        read_only_fields = ("id", "created_at")
