from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from journeys.models import Journey
from notifications.services import send_push
from ride_requests.models import RideRequest
from ride_requests.serializers import RideRequestSerializer
from ride_requests.services import cancel_request, decide_request


def _send_push_best_effort(user, title, body, data):
    try:
        send_push(user, title, body, data)
    except Exception:
        # Push transport failures must not affect a committed ride-request change.
        return


def _is_duplicate_request_integrity_error(error):
    messages = [str(error)]
    if error.__cause__ is not None:
        messages.append(str(error.__cause__))
    message = " ".join(messages).lower()
    if "unique_passenger_journey_request" in message:
        return True
    return "unique constraint failed" in message and "journey_id" in message and "passenger_id" in message


class RideRequestCreateView(generics.CreateAPIView):
    serializer_class = RideRequestSerializer

    def perform_create(self, serializer):
        journey_id = serializer.validated_data["journey"].pk
        try:
            with transaction.atomic():
                journey = Journey.objects.select_for_update().get(pk=journey_id)
                if journey.driver_id == self.request.user.pk:
                    raise ValidationError({"journey": "You cannot request your own journey."})
                if journey.departure_time <= timezone.now():
                    raise ValidationError({"journey": "This journey has already departed."})

                seats_requested = serializer.validated_data.get("seats_requested", 1)
                if journey.status != Journey.Status.OPEN or journey.available_seats < seats_requested:
                    raise ValidationError({"seats": "This journey has insufficient seats or is unavailable."})

                ride_request = serializer.save(passenger=self.request.user)
                transaction.on_commit(
                    lambda driver=journey.driver, journey_id=journey.pk, request_id=ride_request.pk: _send_push_best_effort(
                        driver,
                        "New ride request",
                        "A passenger wants to join your journey.",
                        {"journey_id": journey_id, "request_id": request_id},
                    )
                )
        except Journey.DoesNotExist:
            raise NotFound("Journey not found.")
        except IntegrityError as error:
            if _is_duplicate_request_integrity_error(error):
                raise ValidationError({"journey": "You have already requested this journey."})
            raise


class MyRideRequestsView(generics.ListAPIView):
    serializer_class = RideRequestSerializer

    def get_queryset(self):
        return RideRequest.objects.filter(passenger=self.request.user).select_related("journey")


class JourneyRideRequestsView(generics.ListAPIView):
    serializer_class = RideRequestSerializer

    def get_queryset(self):
        journey_id = self.kwargs["journey_id"]
        try:
            journey = Journey.objects.get(pk=journey_id)
        except Journey.DoesNotExist:
            raise NotFound("Journey not found.")
        if journey.driver_id != self.request.user.pk:
            raise PermissionDenied("Only the journey owner can view requests.")
        return RideRequest.objects.filter(journey=journey).select_related("passenger")


class DecideRideRequestView(APIView):
    def post(self, request, request_id, decision):
        if decision not in ("accept", "reject"):
            raise NotFound()
        result = decide_request(request_id=request_id, driver=request.user, accept=decision == "accept")
        return Response({"success": True, "data": RideRequestSerializer(result).data})


class CancelRideRequestView(APIView):
    def post(self, request, request_id):
        result = cancel_request(request_id=request_id, passenger=request.user)
        return Response({"success": True, "data": RideRequestSerializer(result).data})
