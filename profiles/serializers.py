
from rest_framework import serializers
from profiles.models import Profile, DriverVehicle, DriverVerification


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "id",
            "full_name",
            "phone_number",
            "university",
            "student_id",
            "age",
            "gender",
            "section",
            "is_driver",
            "profile_image_url",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "profile_image_url",
            "created_at",
            "updated_at",
        )


class DriverVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverVehicle
        fields = (
            "id",
            "vehicle_type",
            "model",
            "vehicle_number",
            "capacity",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class DriverVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverVerification
        fields = (
            "id",
            "license_number",
            "citizenship_number",
            "license_image_urls",
            "citizenship_image_urls",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "created_at",
            "updated_at",
        )
