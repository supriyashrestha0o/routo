
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        "accounts.RouteUser",
        on_delete=models.CASCADE,
        related_name="profile",
    )

    full_name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=30, blank=True)
    university = models.CharField(max_length=160, blank=True)
    student_id = models.CharField(max_length=80, blank=True)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=30, blank=True)
    section = models.CharField(max_length=50, blank=True)

    is_driver = models.BooleanField(default=False)

    profile_image_url = models.URLField(max_length=1000, blank=True)
    profile_image_public_id = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name


class DriverVehicle(models.Model):
    class VehicleType(models.TextChoices):
        BIKE = "bike", "Bike"
        SCOOTER = "scooter", "Scooter"
        CAR = "car", "Car"

    user = models.OneToOneField(
        "accounts.RouteUser",
        on_delete=models.CASCADE,
        related_name="vehicle",
    )

    vehicle_type = models.CharField(
        max_length=20,
        choices=VehicleType.choices,
    )
    model = models.CharField(max_length=120)
    vehicle_number = models.CharField(max_length=50)
    capacity = models.PositiveSmallIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vehicle_type} - {self.vehicle_number}"


class DriverVerification(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        "accounts.RouteUser",
        on_delete=models.CASCADE,
        related_name="driver_verification",
    )

    license_number = models.CharField(max_length=100, blank=True)
    citizenship_number = models.CharField(max_length=100, blank=True)

    # Sample document references for the university project.
    license_image_urls = models.JSONField(default=list, blank=True)
    citizenship_image_urls = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.status}"
