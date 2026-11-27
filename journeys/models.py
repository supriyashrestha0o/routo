
from django.db import models
from django.db.models import Q


class Journey(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        FULL = "full", "Full"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    driver = models.ForeignKey(
        "accounts.RouteUser",
        on_delete=models.CASCADE,
        related_name="journeys",
    )
    origin = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    departure_time = models.DateTimeField()
    total_seats = models.PositiveSmallIntegerField()
    available_seats = models.PositiveSmallIntegerField()
    notes = models.CharField(max_length=500, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("departure_time",)
        constraints = [
            models.CheckConstraint(
                condition=Q(total_seats__gte=1),
                name="journey_total_seats_positive",
            ),
            models.CheckConstraint(
                condition=Q(available_seats__lte=models.F("total_seats")),
                name="journey_available_not_over_total",
            ),
        ]


class PassengerTravelPreference(models.Model):
    user = models.OneToOneField(
        "accounts.RouteUser",
        on_delete=models.CASCADE,
        related_name="travel_preference",
    )
    origin = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    departure_time = models.DateTimeField()
    preference = models.CharField(max_length=30)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.origin} to {self.destination}"
