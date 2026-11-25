from rest_framework import generics
from reviews.models import Review
from reviews.serializers import ReviewSerializer
class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    def get_queryset(self):
        queryset = Review.objects.all().select_related("reviewer", "reviewed_user")
        user_id = self.request.query_params.get("user")
        return queryset.filter(reviewed_user_id=user_id) if user_id else queryset.filter(reviewer=self.request.user)
    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)
