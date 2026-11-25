from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from routo.journeys.models import Journey
from routo.journeys.serializers import JourneySerializer

class JourneyListCreateView(generics.ListCreateAPIView):
    serializer_class = JourneySerializer
    def get_queryset(self):
        qs = Journey.objects.select_related("driver").filter(status=Journey.Status.OPEN, departure_time__gte=timezone.now(), available_seats__gt=0)
        for key in ("origin", "destination"):
            value = self.request.query_params.get(key)
            if value:
                qs = qs.filter(**{f"{key}__icontains": value})
        return qs
    def perform_create(self, serializer):
        serializer.save(driver=self.request.user, available_seats=serializer.validated_data["total_seats"])

class JourneyDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = JourneySerializer
    queryset = Journey.objects.select_related("driver")
    def perform_update(self, serializer):
        if serializer.instance.driver_id != self.request.user.pk:
            raise PermissionDenied("Only the journey owner can update this journey.")
        if "total_seats" in serializer.validated_data:
            accepted = serializer.instance.total_seats - serializer.instance.available_seats
            if serializer.validated_data["total_seats"] < accepted:
                raise ValidationError({"total_seats": "Cannot reduce seats below accepted requests."})
            serializer.save(available_seats=serializer.validated_data["total_seats"] - accepted)
        else:
            serializer.save()

class JourneyCancelView(generics.GenericAPIView):
    queryset = Journey.objects.all()
    def post(self, request, *args, **kwargs):
        from rest_framework.response import Response
        obj = self.get_object()
        if obj.driver_id != request.user.pk:
            raise PermissionDenied("Only the journey owner can cancel this journey.")
        obj.status = Journey.Status.CANCELLED
        obj.save(update_fields=["status", "updated_at"])
        return Response({"success": True, "data": JourneySerializer(obj).data})
