
from django.contrib import admin
from profiles.models import Profile, DriverVehicle, DriverVerification


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "university", "student_id", "is_driver")
    search_fields = ("full_name", "university", "student_id")


@admin.register(DriverVehicle)
class DriverVehicleAdmin(admin.ModelAdmin):
    list_display = ("user", "vehicle_type", "model", "vehicle_number", "capacity")
    search_fields = ("vehicle_number", "model")


@admin.register(DriverVerification)
class DriverVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("license_number", "citizenship_number")
