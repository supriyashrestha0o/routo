from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import RouteUser
from journeys.models import Journey
from matches.models import Match
from ride_requests.models import RideRequest


class JourneyApiTests(TestCase):
    def setUp(self):
        self.driver = RouteUser.objects.create(firebase_uid="journey-driver")
        self.passenger = RouteUser.objects.create(firebase_uid="journey-passenger")
        self.client = APIClient()

    def test_driver_creates_and_other_user_retrieves_journey(self):
        self.client.force_authenticate(self.driver)
        created = self.client.post(
            "/api/journeys/",
            {
                "origin": "A",
                "destination": "B",
                "departure_time": (timezone.now() + timedelta(days=1)).isoformat(),
                "total_seats": 2,
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.content)
        journey_id = created.json()["data"]["id"]
        self.client.force_authenticate(self.passenger)
        result = self.client.get("/api/journeys/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["data"][0]["id"], journey_id)

    def test_only_owner_can_update_journey(self):
        journey = Journey.objects.create(
            driver=self.driver,
            origin="A",
            destination="B",
            departure_time=timezone.now() + timedelta(days=1),
            total_seats=2,
            available_seats=2,
        )
        self.client.force_authenticate(self.passenger)
        response = self.client.patch(
            f"/api/journeys/{journey.pk}/",
            {"origin": "X"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_journey_requires_future_departure_and_different_locations(self):
        self.client.force_authenticate(self.driver)
        departed = self.client.post(
            "/api/journeys/",
            {
                "origin": "A",
                "destination": "B",
                "departure_time": (timezone.now() - timedelta(hours=1)).isoformat(),
                "total_seats": 2,
            },
            format="json",
        )
        same_location = self.client.post(
            "/api/journeys/",
            {
                "origin": "A",
                "destination": "a",
                "departure_time": (timezone.now() + timedelta(days=1)).isoformat(),
                "total_seats": 2,
            },
            format="json",
        )

        self.assertEqual(departed.status_code, 400)
        self.assertEqual(same_location.status_code, 400)

    def test_adding_seats_reopens_full_journey(self):
        journey = Journey.objects.create(
            driver=self.driver,
            origin="A",
            destination="B",
            departure_time=timezone.now() + timedelta(days=1),
            total_seats=1,
            available_seats=0,
            status=Journey.Status.FULL,
        )
        self.client.force_authenticate(self.driver)

        response = self.client.patch(
            f"/api/journeys/{journey.pk}/",
            {"total_seats": 2},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.content)
        journey.refresh_from_db()
        self.assertEqual(journey.available_seats, 1)
        self.assertEqual(journey.status, Journey.Status.OPEN)
        self.assertEqual(response.json()["data"]["status"], Journey.Status.OPEN)

    def test_cancelling_journey_cancels_requests_and_removes_matches(self):
        journey = Journey.objects.create(
            driver=self.driver,
            origin="A",
            destination="B",
            departure_time=timezone.now() + timedelta(days=1),
            total_seats=3,
            available_seats=2,
        )
        accepted = RideRequest.objects.create(
            journey=journey,
            passenger=self.passenger,
            seats_requested=1,
            status=RideRequest.Status.ACCEPTED,
        )
        pending = RideRequest.objects.create(
            journey=journey,
            passenger=RouteUser.objects.create(firebase_uid="pending-passenger"),
            seats_requested=1,
            status=RideRequest.Status.PENDING,
        )
        match = Match.objects.create(
            ride_request=accepted,
            journey=journey,
            passenger=self.passenger,
        )
        self.client.force_authenticate(self.driver)

        response = self.client.post(f"/api/journeys/{journey.pk}/cancel/")

        self.assertEqual(response.status_code, 200, response.content)
        journey.refresh_from_db()
        accepted.refresh_from_db()
        pending.refresh_from_db()
        self.assertEqual(journey.status, Journey.Status.CANCELLED)
        self.assertEqual(journey.available_seats, 0)
        self.assertEqual(accepted.status, RideRequest.Status.CANCELLED)
        self.assertEqual(pending.status, RideRequest.Status.CANCELLED)
        self.assertFalse(Match.objects.filter(pk=match.pk).exists())

    def test_completing_journey_preserves_accepted_match(self):
        journey = Journey.objects.create(
            driver=self.driver,
            origin="A",
            destination="B",
            departure_time=timezone.now() - timedelta(hours=1),
            total_seats=2,
            available_seats=1,
        )
        accepted = RideRequest.objects.create(
            journey=journey,
            passenger=self.passenger,
            seats_requested=1,
            status=RideRequest.Status.ACCEPTED,
        )
        pending = RideRequest.objects.create(
            journey=journey,
            passenger=RouteUser.objects.create(firebase_uid="pending-passenger"),
            seats_requested=1,
            status=RideRequest.Status.PENDING,
        )
        Match.objects.create(
            ride_request=accepted,
            journey=journey,
            passenger=self.passenger,
        )
        self.client.force_authenticate(self.driver)

        response = self.client.post(f"/api/journeys/{journey.pk}/complete/")

        self.assertEqual(response.status_code, 200, response.content)
        journey.refresh_from_db()
        accepted.refresh_from_db()
        pending.refresh_from_db()
        self.assertEqual(journey.status, Journey.Status.COMPLETED)
        self.assertEqual(accepted.status, RideRequest.Status.ACCEPTED)
        self.assertEqual(pending.status, RideRequest.Status.CANCELLED)
        self.assertTrue(Match.objects.filter(ride_request=accepted).exists())

    def test_journey_cannot_complete_before_departure(self):
        journey = Journey.objects.create(
            driver=self.driver,
            origin="A",
            destination="B",
            departure_time=timezone.now() + timedelta(hours=1),
            total_seats=2,
            available_seats=2,
        )
        self.client.force_authenticate(self.driver)

        response = self.client.post(f"/api/journeys/{journey.pk}/complete/")

        self.assertEqual(response.status_code, 400)
        journey.refresh_from_db()
        self.assertEqual(journey.status, Journey.Status.OPEN)
