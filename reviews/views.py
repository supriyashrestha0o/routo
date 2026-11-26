from django.db import IntegrityError, transaction
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from reviews.models import Review
from reviews.serializers import ReviewSerializer


class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        queryset = Review.objects.all().select_related("reviewer", "reviewed_user", "journey")
        user_values = self.request.query_params.getlist("user")
        if not user_values:
            return queryset.filter(reviewer=self.request.user)
        if len(user_values) != 1:
            raise ValidationError({"user": "Provide exactly one valid user ID."})
        try:
            user_id = int(user_values[0])
        except (TypeError, ValueError):
            raise ValidationError({"user": "Must be a valid user ID."})
        if user_id <= 0 or user_id > 9223372036854775807:
            raise ValidationError({"user": "Must be a valid user ID."})
        return queryset.filter(reviewed_user_id=user_id)

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                serializer.save(reviewer=self.request.user)
        except IntegrityError as exc:
            raise ValidationError({"journey": "You have already reviewed this user for this journey."}) from exc
