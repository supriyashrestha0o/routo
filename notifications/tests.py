from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import RouteUser
from notifications.models import DeviceToken

class DeviceTokenApiTests(TestCase):
    def test_register_and_remove_own_device_token(self):
        user = RouteUser.objects.create(firebase_uid="token-user")
        client = APIClient(); client.force_authenticate(user)
        response = client.post("/api/notifications/devices/", {"token": "token-123", "platform": "android"}, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        token_id = response.json()["data"]["id"]
        self.assertEqual(DeviceToken.objects.get(pk=token_id).user, user)
        self.assertEqual(client.delete(f"/api/notifications/devices/{token_id}/").status_code, 200)

    def test_registering_existing_token_is_idempotent(self):
        user = RouteUser.objects.create(firebase_uid="token-user")
        client = APIClient(); client.force_authenticate(user)
        first = client.post("/api/notifications/devices/", {"token": "token-123", "platform": "android"}, format="json")
        second = client.post("/api/notifications/devices/", {"token": "token-123", "platform": "ios"}, format="json")

        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(second.status_code, 201, second.content)
        self.assertEqual(first.json()["data"]["id"], second.json()["data"]["id"])
        self.assertEqual(DeviceToken.objects.count(), 1)
        self.assertEqual(DeviceToken.objects.get().platform, "ios")

    def test_registering_existing_token_transfers_ownership(self):
        first_user = RouteUser.objects.create(firebase_uid="token-owner")
        second_user = RouteUser.objects.create(firebase_uid="token-new-owner")
        first_client = APIClient(); first_client.force_authenticate(first_user)
        second_client = APIClient(); second_client.force_authenticate(second_user)
        first_client.post("/api/notifications/devices/", {"token": "token-123"}, format="json")
        response = second_client.post("/api/notifications/devices/", {"token": "token-123"}, format="json")

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(DeviceToken.objects.get().user, second_user)
