from django.db import models

class Profile(models.Model):
    user = models.OneToOneField("accounts.RouteUser", on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=30, blank=True)
    university = models.CharField(max_length=160, blank=True)
    student_id = models.CharField(max_length=80, blank=True)
    is_driver = models.BooleanField(default=False)
    profile_image_url = models.URLField(max_length=1000, blank=True)
    profile_image_public_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
