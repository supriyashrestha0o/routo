from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class Review(models.Model):
    reviewer = models.ForeignKey("accounts.RouteUser", on_delete=models.CASCADE, related_name="reviews_written")
    reviewed_user = models.ForeignKey("accounts.RouteUser", on_delete=models.CASCADE, related_name="reviews_received")
    journey = models.ForeignKey("journeys.Journey", null=True, blank=True, on_delete=models.SET_NULL, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.CharField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=("reviewer", "reviewed_user", "journey"), name="unique_review_per_journey")]
