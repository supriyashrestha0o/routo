from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import RouteUser
from journeys.models import Journey
from matches.models import Match
from ride_requests.models import RideRequest
from reviews.models import Review


class ReviewApiTests(TestCase):
    def setUp(self):
        self.driver = RouteUser.objects.create(
            firebase_uid="review-driver",
            email="driver@example.com",
        )
        self.passenger = RouteUser.objects.create(
            firebase_uid="review-passenger",
            email="passenger@example.com",
        )
        self.outsider = RouteUser.objects.create(
            firebase_uid="review-outsider",
            email="outsider@example.com",
        )
        self.journey = Journey.objects.create(
            driver=self.driver,
            origin="A",
            destination="B",
            departure_time=timezone.now() - timedelta(hours=1),
            total_seats=2,
            available_seats=1,
            status=Journey.Status.COMPLETED,
        )
        self.ride_request = RideRequest.objects.create(
            journey=self.journey,
            passenger=self.passenger,
            seats_requested=1,
            status=RideRequest.Status.ACCEPTED,
        )
        Match.objects.create(
            ride_request=self.ride_request,
            journey=self.journey,
            passenger=self.passenger,
        )
        self.client = APIClient()

    def create_review(self, reviewer, reviewed_user, journey=None):
        self.client.force_authenticate(reviewer)
        return self.client.post(
            "/api/reviews/",
            {
                "reviewed_user": reviewed_user.pk,
                "journey": (journey or self.journey).pk,
                "rating": 5,
                "comment": "On time",
            },
            format="json",
        )

    def test_driver_can_review_accepted_passenger(self):
        response = self.create_review(self.driver, self.passenger)

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Review.objects.count(), 1)

    def test_passenger_can_review_driver(self):
        response = self.create_review(self.passenger, self.driver)

        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Review.objects.get().reviewed_user, self.driver)

    def test_self_review_is_rejected(self):
        response = self.create_review(self.driver, self.driver)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Review.objects.exists())

    def test_unrelated_user_cannot_review(self):
        response = self.create_review(self.outsider, self.driver)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Review.objects.exists())

    def test_review_requires_completed_journey(self):
        self.journey.status = Journey.Status.OPEN
        self.journey.save(update_fields=("status",))

        response = self.create_review(self.driver, self.passenger)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Review.objects.exists())

    def test_duplicate_review_returns_validation_error(self):
        first = self.create_review(self.driver, self.passenger)
        second = self.create_review(self.driver, self.passenger)

        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(Review.objects.count(), 1)

    def test_invalid_user_filter_returns_validation_error(self):
        self.client.force_authenticate(self.driver)

        response = self.client.get("/api/reviews/?user=not-an-id")

        self.assertEqual(response.status_code, 400)
        self.assertIn("user", response.json()["error"])
