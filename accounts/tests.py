from django.test import TestCase
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIClient

from accounts.authentication import sync_route_user
from accounts.models import BlockedFirebaseIdentity, RouteUser


class AccountApiTests(TestCase):
    def test_authenticated_user_is_linked_by_firebase_uid(self):
        user = RouteUser.objects.create(firebase_uid="firebase-a", email="a@example.com")
        client = APIClient(); client.force_authenticate(user)
        response = client.get("/api/accounts/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["firebase_uid"], "firebase-a")

    def test_protected_route_rejects_anonymous_user(self):
        self.assertEqual(APIClient().get("/api/accounts/me/").status_code, 401)

    def test_sync_route_user_creates_firebase_account(self):
        user = sync_route_user({"uid": "firebase-new", "email": "new@example.com"})

        self.assertEqual(user.firebase_uid, "firebase-new")
        self.assertEqual(user.email, "new@example.com")

    def test_sync_route_user_preserves_email_when_claim_is_missing(self):
        user = RouteUser.objects.create(
            firebase_uid="firebase-existing",
            email="existing@example.com",
        )

        synced = sync_route_user({"uid": user.firebase_uid})

        synced.refresh_from_db()
        self.assertEqual(synced.email, "existing@example.com")

    def test_sync_route_user_does_not_update_unchanged_account(self):
        user = RouteUser.objects.create(
            firebase_uid="firebase-unchanged",
            email="unchanged@example.com",
        )
        original_updated_at = user.updated_at

        synced = sync_route_user(
            {"uid": user.firebase_uid, "email": user.email}
        )

        synced.refresh_from_db()
        self.assertEqual(synced.updated_at, original_updated_at)

    def test_sync_route_user_rejects_blocked_firebase_identity(self):
        BlockedFirebaseIdentity.objects.create(
            firebase_uid="firebase-blocked",
            email="blocked@example.com",
            reason="Reported user",
        )

        with self.assertRaises(AuthenticationFailed):
            sync_route_user({"uid": "firebase-blocked"})
