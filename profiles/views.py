
from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from profiles.models import Profile, DriverVehicle, DriverVerification
from profiles.serializers import (
    ProfileSerializer,
    DriverVehicleSerializer,
    DriverVerificationSerializer,
)
from profiles.services import default_profile_full_name

from journeys.models import Journey, PassengerTravelPreference
from journeys.serializers import JourneySerializer
from journeys.preference_serializers import PassengerTravelPreferenceSerializer


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(
            user=self.request.user,
            defaults={
                "full_name": default_profile_full_name(self.request.user)
            },
        )
        return profile


class RegistrationStatusView(APIView):

    def get(self, request):
        profile = Profile.objects.filter(user=request.user).first()

        if profile is None:
            return Response({
                "success": True,
                "completed": False,
                "profile": None,
                "journey": None,
                "travel_preference": None,
                "vehicle": None,
                "verification": None,
            })

        if profile.is_driver:
            # Registration creates a Journey for drivers. Read an existing
            # record only; a status check must never create registration data.
            journey = Journey.objects.filter(driver=request.user).first()
            vehicle = DriverVehicle.objects.filter(user=request.user).first()
            verification = DriverVerification.objects.filter(
                user=request.user
            ).first()
            travel_preference = None
            completed = journey is not None
        else:
            journey = None
            vehicle = None
            verification = None
            travel_preference = PassengerTravelPreference.objects.filter(
                user=request.user
            ).first()
            completed = travel_preference is not None

        return Response({
            "success": True,
            "completed": completed,
            "profile": ProfileSerializer(profile).data,
            "journey": JourneySerializer(journey).data if journey else None,
            "travel_preference": (
                PassengerTravelPreferenceSerializer(travel_preference).data
                if travel_preference else None
            ),
            "vehicle": DriverVehicleSerializer(vehicle).data if vehicle else None,
            "verification": (
                DriverVerificationSerializer(verification).data
                if verification else None
            ),
        })


class CompleteRegistrationView(APIView):

    @transaction.atomic
    def post(self, request):
        data = request.data

        profile_data = data.get("profile", {})
        vehicle_data = data.get("vehicle", {})
        verification_data = data.get("verification", {})
        journey_data = data.get("journey", {})

        if not isinstance(profile_data, dict) or not isinstance(journey_data, dict):
            return Response(
                {"error": "Profile and journey data must be objects."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile, _ = Profile.objects.get_or_create(
            user=request.user,
            defaults={
                "full_name": default_profile_full_name(request.user)
            },
        )

        profile_serializer = ProfileSerializer(
            profile,
            data=profile_data,
            partial=True,
        )
        profile_serializer.is_valid(raise_exception=True)

        is_driver = profile_serializer.validated_data.get(
            "is_driver",
            profile.is_driver,
        )

        origin = journey_data.get("origin", journey_data.get("pickup"))
        destination = journey_data.get("destination")
        departure_time = journey_data.get(
            "departure_time",
            journey_data.get("departure"),
        )

        if not origin or not destination or not departure_time:
            return Response(
                {
                    "error": (
                        "Pickup, destination and departure time "
                        "are required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        journey_result = None
        vehicle_serializer = None
        verification_serializer = None
        preference_serializer = None
        preference_result = None

        if is_driver:
            if not isinstance(vehicle_data, dict) or not vehicle_data:
                return Response(
                    {"error": "Driver vehicle details are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not isinstance(verification_data, dict) or not verification_data:
                return Response(
                    {"error": "Driver verification details are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            vehicle, vehicle_created = DriverVehicle.objects.get_or_create(
                user=request.user,
                defaults={
                    "vehicle_type": "bike",
                    "model": "",
                    "vehicle_number": "",
                    "capacity": 1,
                },
            )

            vehicle_serializer = DriverVehicleSerializer(
                vehicle,
                data=vehicle_data,
                partial=not vehicle_created,
            )
            vehicle_serializer.is_valid(raise_exception=True)

            verification, verification_created = (
                DriverVerification.objects.get_or_create(
                    user=request.user
                )
            )

            verification_serializer = DriverVerificationSerializer(
                verification,
                data=verification_data,
                partial=not verification_created,
            )
            verification_serializer.is_valid(raise_exception=True)

            capacity = vehicle_serializer.validated_data.get(
                "capacity",
                vehicle.capacity,
            )

            journey_payload = {
                "origin": origin,
                "destination": destination,
                "departure_time": departure_time,
                "total_seats": capacity,
                "notes": journey_data.get("notes", ""),
            }

            journey_serializer = JourneySerializer(data=journey_payload)
            journey_serializer.is_valid(raise_exception=True)

            profile_serializer.save(user=request.user)
            vehicle_serializer.save()
            verification_serializer.save()

            journey_result = journey_serializer.save(
                driver=request.user,
                available_seats=capacity,
            )

        else:
            preference = PassengerTravelPreference.objects.filter(
                user=request.user
            ).first()

            preference_payload = {
                "origin": origin,
                "destination": destination,
                "departure_time": departure_time,
                "preference": journey_data.get("preference", ""),
                "latitude": journey_data.get("latitude"),
                "longitude": journey_data.get("longitude"),
            }

            preference_serializer = PassengerTravelPreferenceSerializer(
                preference,
                data=preference_payload,
                partial=preference is not None,
            )
            preference_serializer.is_valid(raise_exception=True)

            profile_serializer.save(user=request.user)
            preference_result = preference_serializer.save(
                user=request.user
            )

        return Response(
            {
                "success": True,
                "message": "Registration details saved successfully.",
                "profile": profile_serializer.data,
                "vehicle": (
                    vehicle_serializer.data if vehicle_serializer else None
                ),
                "verification": (
                    verification_serializer.data
                    if verification_serializer else None
                ),
                "journey": (
                    JourneySerializer(journey_result).data
                    if journey_result else None
                ),
                "travel_preference": (
                    PassengerTravelPreferenceSerializer(
                        preference_result
                    ).data
                    if preference_serializer else None
                ),
            },
            status=status.HTTP_200_OK,
        )
