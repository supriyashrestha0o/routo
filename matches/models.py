from django.db import models

class Match(models.Model):
    ride_request = models.OneToOneField("ride_requests.RideRequest", on_delete=models.CASCADE, related_name="match")
    journey = models.ForeignKey("journeys.Journey", on_delete=models.CASCADE, related_name="matches")
    passenger = models.ForeignKey("accounts.RouteUser", on_delete=models.CASCADE, related_name="matches")
    created_at = models.DateTimeField(auto_now_add=True)
