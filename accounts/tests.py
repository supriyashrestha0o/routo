from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import RouteUser

class AccountApiTests(TestCase):
    def test_authenticated_user_is_linked_by_firebase_uid(self):
        user = RouteUser.objects.create(firebase_uid="firebase-a", email="a@example.com")
        client = APIClient(); client.force_authenticate(user)
        response = client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["firebase_uid"], "firebase-a")
    def test_protected_route_rejects_anonymous_user(self):
        self.assertEqual(APIClient().get("/api/accounts/me/").status_code, 401)
