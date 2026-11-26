from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from journeys.models import Journey
from matches.models import Match
from notifications.services import send_push
from ride_requests.models import RideRequest


def _send_push_best_effort(user, title, body, data):
    try:
        send_push(user, title, body, data)
    except Exception:
        # Push transport failures must not affect a committed ride-request change.
        return


@transaction.atomic
def decide_request(*, request_id, driver, accept):
    try:
        candidate = RideRequest.objects.only("journey_id").get(pk=request_id)
    except RideRequest.DoesNotExist:
        raise NotFound("Ride request not found.")

    journey = Journey.objects.select_for_update().get(pk=candidate.journey_id)
    if journey.driver_id != driver.pk:
        raise PermissionDenied("Only the journey owner can decide this request.")

    try:
        ride_request = RideRequest.objects.select_for_update().select_related("passenger").get(pk=request_id)
    except RideRequest.DoesNotExist:
        raise NotFound("Ride request not found.")
    if ride_request.status != RideRequest.Status.PENDING:
        raise ValidationError({"status": "This request has already been decided."})

    if accept:
        if journey.departure_time <= timezone.now():
            raise ValidationError({"journey": "This journey has already departed."})
        if journey.status != Journey.Status.OPEN or journey.available_seats < ride_request.seats_requested:
            raise ValidationError({"seats": "There are not enough available seats."})

        journey.available_seats -= ride_request.seats_requested
        journey.status = Journey.Status.FULL if journey.available_seats == 0 else Journey.Status.OPEN
        journey.save(update_fields=["available_seats", "status", "updated_at"])

        ride_request.status = RideRequest.Status.ACCEPTED
        ride_request.save(update_fields=["status", "updated_at"])
        Match.objects.get_or_create(ride_request=ride_request, defaults={"journey": journey, "passenger": ride_request.passenger})
        transaction.on_commit(
            lambda passenger=ride_request.passenger, journey_id=journey.pk, request_id=ride_request.pk: _send_push_best_effort(
                passenger,
                "Ride request accepted",
                "Your request was accepted.",
                {"journey_id": journey_id, "request_id": request_id},
            )
        )
    else:
        ride_request.status = RideRequest.Status.REJECTED
        ride_request.save(update_fields=["status", "updated_at"])
        transaction.on_commit(
            lambda passenger=ride_request.passenger, journey_id=journey.pk, request_id=ride_request.pk: _send_push_best_effort(
                passenger,
                "Ride request update",
                "Your ride request was declined.",
                {"journey_id": journey_id, "request_id": request_id},
            )
        )
    return ride_request


@transaction.atomic
def cancel_request(*, request_id, passenger):
    try:
        candidate = RideRequest.objects.only("journey_id").get(pk=request_id)
    except RideRequest.DoesNotExist:
        raise NotFound("Ride request not found.")

    journey = Journey.objects.select_for_update().get(pk=candidate.journey_id)
    try:
        ride_request = RideRequest.objects.select_for_update().select_related("passenger").get(pk=request_id)
    except RideRequest.DoesNotExist:
        raise NotFound("Ride request not found.")

    if ride_request.passenger_id != passenger.pk:
        raise PermissionDenied("Only the passenger can cancel this ride request.")
    if ride_request.status not in (RideRequest.Status.PENDING, RideRequest.Status.ACCEPTED):
        raise ValidationError({"status": "This ride request has already been finalized."})

    if ride_request.status == RideRequest.Status.ACCEPTED:
        if journey.status in (Journey.Status.CANCELLED, Journey.Status.COMPLETED):
            raise ValidationError({"journey": "This journey can no longer be changed."})

        restored_seats = journey.available_seats + ride_request.seats_requested
        if restored_seats > journey.total_seats:
            raise ValidationError({"seats": "Unable to restore the requested seats."})
        journey.available_seats = restored_seats
        journey.status = Journey.Status.FULL if journey.available_seats == 0 else Journey.Status.OPEN
        journey.save(update_fields=["available_seats", "status", "updated_at"])
        Match.objects.filter(ride_request=ride_request).delete()

    ride_request.status = RideRequest.Status.CANCELLED
    ride_request.save(update_fields=["status", "updated_at"])
    transaction.on_commit(
        lambda driver=journey.driver, journey_id=journey.pk, request_id=ride_request.pk: _send_push_best_effort(
            driver,
            "Ride request cancelled",
            "A passenger cancelled their ride request.",
            {"journey_id": journey_id, "request_id": request_id},
        )
    )
    return ride_request
