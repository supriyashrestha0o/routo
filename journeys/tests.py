from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import RouteUser
from journeys.models import Journey

class JourneyApiTests(TestCase):
    def setUp(self):
        self.driver = RouteUser.objects.create(firebase_uid="journey-driver")
        self.passenger = RouteUser.objects.create(firebase_uid="journey-passenger")
        self.client = APIClient()
    def test_driver_creates_and_other_user_retrieves_journey(self):
        self.client.force_authenticate(self.driver)
        created = self.client.post("/api/journeys/", {"origin": "A", "destination": "B", "departure_time": (timezone.now()+timedelta(days=1)).isoformat(), "total_seats": 2}, format="json")
        self.assertEqual(created.status_code, 201, created.content)
        journey_id = created.json()["data"]["id"]
        self.client.force_authenticate(self.passenger)
        result = self.client.get("/api/journeys/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["data"][0]["id"], journey_id)
    def test_only_owner_can_update_journey(self):
        journey = Journey.objects.create(driver=self.driver, origin="A", destination="B", departure_time=timezone.now()+timedelta(days=1), total_seats=2, available_seats=2)
        self.client.force_authenticate(self.passenger)
        response = self.client.patch(f"/api/journeys/{journey.pk}/", {"origin": "X"}, format="json")
        self.assertEqual(response.status_code, 403)
