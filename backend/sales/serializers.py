from rest_framework import serializers

from .models import SaleRecord


class SaleRecordSerializer(serializers.ModelSerializer):
    total_amount = serializers.ReadOnlyField()
    batch_number = serializers.CharField(source="batch.batch_number", read_only=True, default=None)

    class Meta:
        model = SaleRecord
        fields = [
            "id", "batch", "batch_number", "buyer_name", "quantity",
            "price_per_unit", "total_amount", "sale_date", "created_at",
        ]
        read_only_fields = ["id", "total_amount", "created_at"]

    def validate_batch(self, batch):
        request = self.context["request"]
        if batch is not None and batch.farm_id != request.user.farm_id:
            raise serializers.ValidationError("Batch must belong to your farm.")
        return batch
