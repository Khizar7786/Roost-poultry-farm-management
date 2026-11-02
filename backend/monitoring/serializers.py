from rest_framework import serializers

from .models import CountingSession, MortalityEvent, MortalitySource, PricePrediction


class CountingSessionSerializer(serializers.ModelSerializer):
    """UC-01 Chick Counting. `count`/`confidence`/`boxes`/`model_version`/
    `processing_time_ms` are filled in by the view after running local
    inference — the client only ever supplies `batch` + `image`."""

    captured_by_name = serializers.CharField(source="captured_by.get_full_name", read_only=True)

    class Meta:
        model = CountingSession
        fields = [
            "id", "batch", "image", "count", "confidence", "boxes",
            "model_version", "processing_time_ms", "captured_by_name", "created_at",
        ]
        read_only_fields = [
            "id", "count", "confidence", "boxes", "model_version",
            "processing_time_ms", "captured_by_name", "created_at",
        ]

    def validate_batch(self, batch):
        request = self.context["request"]
        if batch.farm_id != request.user.farm_id:
            raise serializers.ValidationError("Batch must belong to your farm.")
        return batch


class MortalityEventSerializer(serializers.ModelSerializer):
    logged_by_name = serializers.CharField(source="logged_by.get_full_name", read_only=True, default=None)

    class Meta:
        model = MortalityEvent
        fields = [
            "id", "batch", "source", "detected_count", "confidence",
            "image", "confirmed", "logged_by_name", "created_at",
        ]
        read_only_fields = ["id", "source", "confidence", "confirmed", "logged_by_name", "created_at"]

    def validate_batch(self, batch):
        request = self.context["request"]
        if batch.farm_id != request.user.farm_id:
            raise serializers.ValidationError("Batch must belong to your farm.")
        return batch

    def create(self, validated_data):
        # Any mortality event entered through this endpoint is by
        # definition user-reported, not AI-detected.
        validated_data["source"] = MortalitySource.MANUAL
        validated_data["confirmed"] = True
        return super().create(validated_data)


class PricePredictionSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source="requested_by.get_full_name", read_only=True)

    class Meta:
        model = PricePrediction
        fields = [
            "id", "horizon_days", "forecast", "summary", "last_known_date",
            "last_known_price_pkr", "model_accuracy", "confidence_threshold",
            "model_version", "requested_by_name", "created_at",
        ]
        read_only_fields = fields


class PricePredictionRequestSerializer(serializers.Serializer):
    """Input for triggering a new forecast (UC-03 main flow step 1)."""

    horizon_days = serializers.IntegerField(min_value=1, max_value=30, default=10)
