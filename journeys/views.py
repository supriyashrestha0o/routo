
from functools import partial

from django.db import transaction
from django.utils import timezone

from rest_framework import generics
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from journeys.models import Journey, PassengerTravelPreference
from journeys.serializers import JourneySerializer
from journeys.preference_serializers import PassengerTravelPreferenceSerializer

from matches.models import Match
from notifications.services import send_push
from ride_requests.models import RideRequest


def _send_push_best_effort(user, title, body, data):
    try:
        send_push(user, title, body, data)
    except Exception:
        # Push transport failures must not affect a committed journey change.
        return


class JourneyListCreateView(generics.ListCreateAPIView):
    serializer_class = JourneySerializer

    def get_queryset(self):
        qs = Journey.objects.select_related("driver").filter(
            status=Journey.Status.OPEN,
            departure_time__gte=timezone.now(),
            available_seats__gt=0,
        )

        for key in ("origin", "destination"):
            value = self.request.query_params.get(key)
            if value:
                qs = qs.filter(**{f"{key}__icontains": value})

        return qs

    def perform_create(self, serializer):
        serializer.save(
            driver=self.request.user,
            available_seats=serializer.validated_data["total_seats"],
        )


class JourneyDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = JourneySerializer
    queryset = Journey.objects.select_related("driver")

    def perform_update(self, serializer):
        journey_id = serializer.instance.pk

        with transaction.atomic():
            journey = Journey.objects.select_for_update().get(pk=journey_id)

            if journey.driver_id != self.request.user.pk:
                raise PermissionDenied(
                    "Only the journey owner can update this journey."
                )

            if journey.status in (
                Journey.Status.CANCELLED,
                Journey.Status.COMPLETED,
            ):
                raise ValidationError({
                    "status": (
                        f"A {journey.get_status_display().lower()} "
                        "journey cannot be updated."
                    )
                })

            accepted_seats = journey.total_seats - journey.available_seats
            total_seats = serializer.validated_data.get(
                "total_seats", journey.total_seats
            )

            if total_seats < accepted_seats:
                raise ValidationError({
                    "total_seats": "Cannot reduce seats below accepted requests."
                })

            origin = serializer.validated_data.get("origin", journey.origin)
            destination = serializer.validated_data.get(
                "destination", journey.destination
            )

            if origin.strip().casefold() == destination.strip().casefold():
                raise ValidationError({
                    "destination": "Origin and destination must be different."
                })

            departure_time = serializer.validated_data.get(
                "departure_time", journey.departure_time
            )

            if departure_time <= timezone.now():
                raise ValidationError({
                    "departure_time": "Departure time must be in the future."
                })

            journey.available_seats = total_seats - accepted_seats
            journey.status = (
                Journey.Status.FULL
                if journey.available_seats == 0
                else Journey.Status.OPEN
            )

            serializer.instance = journey

            update_fields = (
                list(serializer.validated_data)
                + ["available_seats", "status", "updated_at"]
            )

            serializer.save(
                update_fields=list(dict.fromkeys(update_fields))
            )


class JourneyCancelView(generics.GenericAPIView):
    queryset = Journey.objects.all()

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                journey = Journey.objects.select_for_update().get(
                    pk=self.kwargs["pk"]
                )

                if journey.driver_id != request.user.pk:
                    raise PermissionDenied(
                        "Only the journey owner can cancel this journey."
                    )

                if journey.status == Journey.Status.COMPLETED:
                    raise ValidationError({
                        "status": "A completed journey cannot be cancelled."
                    })

                affected_requests = list(
                    RideRequest.objects.select_for_update()
                    .filter(
                        journey=journey,
                        status__in=(
                            RideRequest.Status.PENDING,
                            RideRequest.Status.ACCEPTED,
                        ),
                    )
                    .select_related("passenger")
                )

                if affected_requests:
                    request_ids = [
                        ride_request.pk
                        for ride_request in affected_requests
                    ]

                    Match.objects.filter(
                        ride_request_id__in=request_ids
                    ).delete()

                    RideRequest.objects.filter(
                        pk__in=request_ids
                    ).update(
                        status=RideRequest.Status.CANCELLED,
                        updated_at=timezone.now(),
                    )

                journey.status = Journey.Status.CANCELLED
                journey.available_seats = 0

                journey.save(
                    update_fields=[
                        "status",
                        "available_seats",
                        "updated_at",
                    ]
                )

                for ride_request in affected_requests:
                    transaction.on_commit(
                        partial(
                            _send_push_best_effort,
                            ride_request.passenger,
                            "Journey cancelled",
                            "Your journey was cancelled.",
                            {
                                "journey_id": journey.pk,
                                "request_id": ride_request.pk,
                            },
                        )
                    )

        except Journey.DoesNotExist:
            raise NotFound("Journey not found.")

        return Response({
            "success": True,
            "data": JourneySerializer(journey).data,
        })


class JourneyCompleteView(generics.GenericAPIView):
    queryset = Journey.objects.all()

    def post(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                journey = Journey.objects.select_for_update().get(
                    pk=self.kwargs["pk"]
                )

                if journey.driver_id != request.user.pk:
                    raise PermissionDenied(
                        "Only the journey owner can complete this journey."
                    )

                if journey.status == Journey.Status.CANCELLED:
                    raise ValidationError({
                        "status": "A cancelled journey cannot be completed."
                    })

                if journey.departure_time > timezone.now():
                    raise ValidationError({
                        "status": (
                            "A journey cannot be completed before "
                            "its departure time."
                        )
                    })

                affected_requests = list(
                    RideRequest.objects.select_for_update()
                    .filter(
                        journey=journey,
                        status__in=(
                            RideRequest.Status.PENDING,
                            RideRequest.Status.ACCEPTED,
                        ),
                    )
                    .select_related("passenger")
                )

                pending_ids = [
                    ride_request.pk
                    for ride_request in affected_requests
                    if ride_request.status == RideRequest.Status.PENDING
                ]

                if pending_ids:
                    RideRequest.objects.filter(
                        pk__in=pending_ids
                    ).update(
                        status=RideRequest.Status.CANCELLED,
                        updated_at=timezone.now(),
                    )

                journey.status = Journey.Status.COMPLETED
                journey.save(update_fields=["status", "updated_at"])

                for ride_request in affected_requests:
                    transaction.on_commit(
                        partial(
                            _send_push_best_effort,
                            ride_request.passenger,
                            "Journey completed",
                            "Your journey has been completed.",
                            {
                                "journey_id": journey.pk,
                                "request_id": ride_request.pk,
                            },
                        )
                    )

        except Journey.DoesNotExist:
            raise NotFound("Journey not found.")

        return Response({
            "success": True,
            "data": JourneySerializer(journey).data,
        })


class PassengerTravelPreferenceView(generics.GenericAPIView):
    serializer_class = PassengerTravelPreferenceSerializer

    def get_object(self):
        try:
            return PassengerTravelPreference.objects.get(
                user=self.request.user
            )
        except PassengerTravelPreference.DoesNotExist:
            raise NotFound("Travel preference not found.")

    def get(self, request, *args, **kwargs):
        preference = self.get_object()
        serializer = self.get_serializer(preference)

        return Response({
            "success": True,
            "data": serializer.data,
        })

    def post(self, request, *args, **kwargs):
        existing = PassengerTravelPreference.objects.filter(
            user=request.user
        ).first()

        serializer = self.get_serializer(
            existing,
            data=request.data,
            partial=existing is not None,
        )

        serializer.is_valid(raise_exception=True)

        preference = serializer.save(user=request.user)

        return Response({
            "success": True,
            "data": self.get_serializer(preference).data,
        })
