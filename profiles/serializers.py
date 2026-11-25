from rest_framework import serializers
from profiles.models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "full_name", "phone_number", "university", "student_id", "is_driver", "profile_image_url", "created_at", "updated_at")
        read_only_fields = ("id", "profile_image_url", "created_at", "updated_at")
