from rest_framework import generics
from reports.models import Report
from reports.serializers import ReportSerializer
class ReportListCreateView(generics.ListCreateAPIView):
    serializer_class = ReportSerializer
    def get_queryset(self):
        return Report.objects.filter(reporter=self.request.user).select_related("reported_user", "journey")
    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
