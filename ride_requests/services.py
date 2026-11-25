from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from journeys.models import Journey
from matches.models import Match
from notifications.services import send_push
from ride_requests.models import RideRequest

@transaction.atomic
def decide_request(*, request_id, driver, accept):
    try:
        candidate = RideRequest.objects.select_related("journey", "passenger").get(pk=request_id)
    except RideRequest.DoesNotExist:
        raise NotFound("Ride request not found.")
    journey = Journey.objects.select_for_update().get(pk=candidate.journey_id)
    if journey.driver_id != driver.pk:
        raise PermissionDenied("Only the journey owner can decide this request.")
    ride_request = RideRequest.objects.select_for_update().select_related("passenger").get(pk=request_id)
    if ride_request.status != RideRequest.Status.PENDING:
        raise ValidationError({"status": "This request has already been decided."})
    if accept:
        if journey.status != Journey.Status.OPEN or journey.available_seats < ride_request.seats_requested:
            raise ValidationError({"seats": "There are not enough available seats."})
        Journey.objects.filter(pk=journey.pk).update(available_seats=F("available_seats") - ride_request.seats_requested)
        journey.refresh_from_db()
        if journey.available_seats == 0:
            journey.status = Journey.Status.FULL
            journey.save(update_fields=["status", "updated_at"])
        ride_request.status = RideRequest.Status.ACCEPTED
        ride_request.save(update_fields=["status", "updated_at"])
        Match.objects.get_or_create(ride_request=ride_request, defaults={"journey": journey, "passenger": ride_request.passenger})
        transaction.on_commit(lambda: send_push(ride_request.passenger, "Ride request accepted", "Your request was accepted.", {"journey_id": journey.pk, "request_id": ride_request.pk}))
    else:
        ride_request.status = RideRequest.Status.REJECTED
        ride_request.save(update_fields=["status", "updated_at"])
        transaction.on_commit(lambda: send_push(ride_request.passenger, "Ride request update", "Your ride request was declined.", {"journey_id": journey.pk, "request_id": ride_request.pk}))
    return ride_request
