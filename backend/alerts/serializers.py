from rest_framework import serializers

from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    batch_number = serializers.CharField(source="batch.batch_number", read_only=True, default=None)
    is_overdue_for_escalation = serializers.ReadOnlyField()

    class Meta:
        model = Alert
        fields = [
            "id", "batch", "batch_number", "alert_type", "severity", "message",
            "acknowledged", "acknowledged_at", "escalated", "is_overdue_for_escalation", "created_at",
        ]
        read_only_fields = fields
