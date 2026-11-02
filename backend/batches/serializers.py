from rest_framework import serializers

from .models import BatchStatus, ChickBatch


class ChickBatchSerializer(serializers.ModelSerializer):
    age_days = serializers.ReadOnlyField()
    mortality_count = serializers.ReadOnlyField()
    mortality_rate_pct = serializers.ReadOnlyField()
    shed_name = serializers.CharField(source="shed.name", read_only=True, default=None)

    class Meta:
        model = ChickBatch
        fields = [
            "id", "batch_number", "shed", "shed_name", "arrival_date",
            "initial_count", "current_count", "status", "age_days",
            "mortality_count", "mortality_rate_pct", "created_by", "created_at",
        ]
        read_only_fields = ["id", "current_count", "created_by", "created_at"]

    def validate_shed(self, shed):
        if shed is not None and shed.farm_id != self.context["request"].user.farm_id:
            raise serializers.ValidationError("Shed must belong to your farm.")
        return shed

    def validate_status(self, value):
        if value not in BatchStatus.values:
            raise serializers.ValidationError("Invalid status.")
        return value
