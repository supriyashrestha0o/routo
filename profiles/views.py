from rest_framework import generics
from profiles.models import Profile
from profiles.serializers import ProfileSerializer

class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user, defaults={"full_name": self.request.user.email or "Student"})
        return profile
