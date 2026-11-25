from rest_framework import serializers
from routo.reports.models import Report
class ReportSerializer(serializers.ModelSerializer):
    reporter_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Report
        fields = ("id", "reporter_id", "reported_user", "journey", "description", "status", "created_at")
        read_only_fields = ("id", "reporter_id", "status", "created_at")
    def validate(self, attrs):
        if attrs.get("reported_user") == self.context["request"].user:
            raise serializers.ValidationError({"reported_user": "You cannot report yourself."})
        return attrs
