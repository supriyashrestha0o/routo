from django.db import models

class RideRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"
    journey = models.ForeignKey("journeys.Journey", on_delete=models.CASCADE, related_name="ride_requests")
    passenger = models.ForeignKey("accounts.RouteUser", on_delete=models.CASCADE, related_name="ride_requests")
    seats_requested = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ("-created_at",)
        constraints = [models.UniqueConstraint(fields=("journey", "passenger"), name="unique_passenger_journey_request"), models.CheckConstraint(condition=models.Q(seats_requested__gte=1), name="request_seats_positive")]
