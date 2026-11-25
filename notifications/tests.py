from django.test import TestCase
from rest_framework.test import APIClient
from routo.accounts.models import RouteUser
from routo.notifications.models import DeviceToken

class DeviceTokenApiTests(TestCase):
    def test_register_and_remove_own_device_token(self):
        user = RouteUser.objects.create(firebase_uid="token-user")
        client = APIClient(); client.force_authenticate(user)
        response = client.post("/api/notifications/devices/", {"token": "token-123", "platform": "android"}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        token_id = response.json()["data"]["id"]
        self.assertEqual(DeviceToken.objects.get(pk=token_id).user, user)
        self.assertEqual(client.delete(f"/api/notifications/devices/{token_id}/").status_code, 200)
