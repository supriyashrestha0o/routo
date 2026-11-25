from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from routo.notifications.models import DeviceToken
from routo.notifications.serializers import DeviceTokenSerializer

class DeviceTokenListCreateView(generics.ListCreateAPIView):
    serializer_class = DeviceTokenSerializer
    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        token = serializer.validated_data["token"]
        DeviceToken.objects.filter(token=token).update(user=self.request.user, active=True, platform=serializer.validated_data.get("platform", ""))
        if not DeviceToken.objects.filter(token=token, user=self.request.user).exists():
            serializer.save(user=self.request.user)

class DeviceTokenDeleteView(APIView):
    def delete(self, request, token_id):
        DeviceToken.objects.filter(pk=token_id, user=request.user).delete()
        return Response({"success": True, "data": None})
