from rest_framework import serializers

from .models import VaccinationRecord, VaccinationStatus


class VaccinationRecordSerializer(serializers.ModelSerializer):
    administered_by_name = serializers.CharField(source="administered_by.get_full_name", read_only=True)

    class Meta:
        model = VaccinationRecord
        fields = [
            "id", "batch", "vaccine_name", "scheduled_date", "administered_date",
            "status", "administered_by_name", "notes",
        ]
        read_only_fields = ["id", "administered_date", "status", "administered_by_name"]

    def validate_batch(self, batch):
        if batch.farm_id != self.context["request"].user.farm_id:
            raise serializers.ValidationError("Batch must belong to your farm.")
        return batch

    def validate_status(self, value):
        if value not in VaccinationStatus.values:
            raise serializers.ValidationError("Invalid status.")
        return value
