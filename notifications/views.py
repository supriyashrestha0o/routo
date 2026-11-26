from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from notifications.models import DeviceToken
from notifications.serializers import DeviceTokenSerializer

class DeviceTokenListCreateView(generics.ListCreateAPIView):
    serializer_class = DeviceTokenSerializer

    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        token = serializer.validated_data["token"]
        instance, _ = DeviceToken.objects.update_or_create(
            token_hash=DeviceToken.hash_token(token),
            defaults={
                "token": token,
                "user": self.request.user,
                "active": True,
                "platform": serializer.validated_data.get("platform", ""),
            },
        )
        # Ensure the create response includes the persisted id, including for
        # an idempotent re-registration of an existing token.
        serializer.instance = instance

class DeviceTokenDeleteView(APIView):
    def delete(self, request, token_id):
        DeviceToken.objects.filter(pk=token_id, user=request.user).delete()
        return Response({"success": True, "data": None})
