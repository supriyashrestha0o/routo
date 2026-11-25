from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from accounts.models import RouteUser
from journeys.models import Journey
from ride_requests.models import RideRequest

class RideRequestApiTests(TestCase):
    def setUp(self):
        self.driver = RouteUser.objects.create(firebase_uid="request-driver")
        self.passenger = RouteUser.objects.create(firebase_uid="request-passenger")
        self.other = RouteUser.objects.create(firebase_uid="request-other")
        self.journey = Journey.objects.create(driver=self.driver, origin="A", destination="B", departure_time=timezone.now()+timedelta(days=1), total_seats=1, available_seats=1)
        self.client = APIClient()
    def request_ride(self):
        self.client.force_authenticate(self.passenger)
        return self.client.post("/api/ride-requests/", {"journey": self.journey.pk, "seats_requested": 1}, format="json")
    def test_passenger_request_and_duplicate_prevention(self):
        self.assertEqual(self.request_ride().status_code, 201)
        self.assertEqual(self.request_ride().status_code, 400)
        self.assertEqual(RideRequest.objects.count(), 1)
    def test_cannot_request_own_journey(self):
        self.client.force_authenticate(self.driver)
        response = self.client.post("/api/ride-requests/", {"journey": self.journey.pk}, format="json")
        self.assertEqual(response.status_code, 400)
    def test_accept_consumes_seat_once_and_creates_match(self):
        request = self.request_ride().json()["data"]["id"]
        self.client.force_authenticate(self.driver)
        response = self.client.post(f"/api/ride-requests/{request}/accept/")
        self.assertEqual(response.status_code, 200, response.content)
        self.journey.refresh_from_db()
        self.assertEqual(self.journey.available_seats, 0)
        self.assertEqual(self.journey.status, Journey.Status.FULL)
        self.assertTrue(RideRequest.objects.get(pk=request).match)
        self.assertEqual(self.client.post(f"/api/ride-requests/{request}/accept/").status_code, 400)
    def test_only_owner_can_decide_request(self):
        request = self.request_ride().json()["data"]["id"]
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(f"/api/ride-requests/{request}/accept/").status_code, 403)
    def test_insufficient_seats_rejected(self):
        self.client.force_authenticate(self.passenger)
        response = self.client.post("/api/ride-requests/", {"journey": self.journey.pk, "seats_requested": 2}, format="json")
        self.assertEqual(response.status_code, 400)
    def test_driver_and_passenger_request_lists(self):
        request = self.request_ride().json()["data"]["id"]
        self.client.force_authenticate(self.driver)
        self.assertEqual(len(self.client.get(f"/api/ride-requests/journeys/{self.journey.pk}/").json()["data"]), 1)
        self.client.force_authenticate(self.passenger)
        self.assertEqual(self.client.get("/api/ride-requests/mine/").json()["data"][0]["id"], request)

    def test_reject_keeps_seats_and_updates_passenger(self):
        request = self.request_ride().json()["data"]["id"]
        self.client.force_authenticate(self.driver)
        response = self.client.post(f"/api/ride-requests/{request}/reject/")
        self.assertEqual(response.status_code, 200)
        self.journey.refresh_from_db()
        self.assertEqual(self.journey.available_seats, 1)
        self.assertEqual(RideRequest.objects.get(pk=request).status, RideRequest.Status.REJECTED)

    def test_new_request_schedules_driver_push(self):
        self.client.force_authenticate(self.passenger)
        with patch("ride_requests.views.send_push") as send_push:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post("/api/ride-requests/", {"journey": self.journey.pk}, format="json")
        self.assertEqual(response.status_code, 201)
        send_push.assert_called_once()

    def test_accept_schedules_passenger_push(self):
        request = self.request_ride().json()["data"]["id"]
        self.client.force_authenticate(self.driver)
        with patch("ride_requests.services.send_push") as send_push:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(f"/api/ride-requests/{request}/accept/")
        self.assertEqual(response.status_code, 200)
        send_push.assert_called_once()
