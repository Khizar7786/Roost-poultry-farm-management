from decimal import Decimal

from rest_framework import serializers

from .models import FeedConsumptionLog, FeedStock


class FeedStockSerializer(serializers.ModelSerializer):
    needs_reorder = serializers.ReadOnlyField()

    class Meta:
        model = FeedStock
        fields = ["id", "feed_type", "quantity_kg", "reorder_threshold_kg", "needs_reorder", "last_updated"]
        read_only_fields = ["id", "last_updated"]
        extra_kwargs = {
            "quantity_kg": {"min_value": Decimal("0.00")},
            "reorder_threshold_kg": {"min_value": Decimal("0.00")},
        }


class FeedConsumptionLogSerializer(serializers.ModelSerializer):
    logged_by_name = serializers.CharField(source="logged_by.get_full_name", read_only=True)

    class Meta:
        model = FeedConsumptionLog
        fields = ["id", "batch", "feed_stock", "quantity_kg", "log_date", "logged_by_name", "created_at"]
        read_only_fields = ["id", "logged_by_name", "created_at"]
        extra_kwargs = {"quantity_kg": {"min_value": Decimal("0.01")}}

    def validate(self, attrs):
        feed_stock = attrs["feed_stock"]
        batch = attrs["batch"]
        request = self.context["request"]
        if feed_stock.farm_id != request.user.farm_id or batch.farm_id != request.user.farm_id:
            raise serializers.ValidationError("Feed stock and batch must belong to your farm.")
        if attrs["quantity_kg"] > feed_stock.quantity_kg:
            raise serializers.ValidationError("Not enough feed stock remaining for this log entry.")
        return attrs
