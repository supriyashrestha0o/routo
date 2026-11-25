from django.db import IntegrityError, transaction
from rest_framework import generics
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from journeys.models import Journey
from notifications.services import send_push
from ride_requests.models import RideRequest
from ride_requests.serializers import RideRequestSerializer
from ride_requests.services import decide_request

class RideRequestCreateView(generics.CreateAPIView):
    serializer_class = RideRequestSerializer
    def perform_create(self, serializer):
        journey_id = serializer.validated_data["journey"].pk
        try:
            with transaction.atomic():
                journey = Journey.objects.select_for_update().get(pk=journey_id)
                if journey.driver_id == self.request.user.pk:
                    raise ValidationError({"journey": "You cannot request your own journey."})
                if journey.status != Journey.Status.OPEN or journey.available_seats < serializer.validated_data.get("seats_requested", 1):
                    raise ValidationError({"seats": "This journey has insufficient seats or is unavailable."})
                ride_request = serializer.save(passenger=self.request.user)
        except Journey.DoesNotExist:
            raise NotFound("Journey not found.")
        except IntegrityError:
            raise ValidationError({"journey": "You have already requested this journey."})
        transaction.on_commit(lambda: send_push(journey.driver, "New ride request", "A passenger wants to join your journey.", {"journey_id": journey.pk, "request_id": ride_request.pk}))

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
