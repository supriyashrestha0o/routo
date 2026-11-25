from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from routo.accounts.serializers import AccountSerializer

class AccountLinkView(APIView):
    """The verified Firebase identity is linked automatically at authentication."""
    def post(self, request):
        return Response({"success": True, "data": AccountSerializer(request.user).data}, status=status.HTTP_200_OK)

class MeView(APIView):
    def get(self, request):
        return Response({"success": True, "data": AccountSerializer(request.user).data})
