from django.db import models


class Report(models.Model):
    reporter = models.ForeignKey(
        "accounts.RouteUser",
        on_delete=models.CASCADE,
        related_name="reports_filed",
    )
    reported_user = models.ForeignKey(
        "accounts.RouteUser",
        on_delete=models.CASCADE,
        related_name="reports_received",
    )
    journey = models.ForeignKey(
        "journeys.Journey",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reports",
    )
    description = models.TextField(max_length=2000)
    status = models.CharField(max_length=16, default="open")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report {self.pk}: {self.reporter} -> {self.reported_user}"
