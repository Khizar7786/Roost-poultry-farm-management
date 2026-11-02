from django.db import transaction
from django.db.models import F
from django.db.models.functions import Round
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.permissions import IsFarmMember, IsFarmOwnerOrEmployeeReadOnly

from .models import FeedConsumptionLog, FeedStock
from .serializers import FeedConsumptionLogSerializer, FeedStockSerializer


class FeedStockListCreateView(generics.ListCreateAPIView):
    """GET: Owner + Employee. POST (restock): Owner only."""

    serializer_class = FeedStockSerializer
    permission_classes = [IsFarmOwnerOrEmployeeReadOnly]

    def get_queryset(self):
        return FeedStock.objects.filter(farm=self.request.user.farm)

    def perform_create(self, serializer):
        if not self.request.user.is_owner:
            raise PermissionDenied("Only the farm owner can add new feed stock.")
        serializer.save(farm=self.request.user.farm)


class FeedConsumptionLogListCreateView(generics.ListCreateAPIView):
    """Employees log day-to-day consumption; Owners can too. This
    decrements the linked FeedStock atomically."""

    serializer_class = FeedConsumptionLogSerializer
    permission_classes = [IsFarmMember]

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        return FeedConsumptionLog.objects.filter(batch__farm=self.request.user.farm).select_related(
            "batch", "feed_stock", "logged_by"
        )

    @transaction.atomic
    def perform_create(self, serializer):
        stock = serializer.validated_data["feed_stock"]
        quantity = serializer.validated_data["quantity_kg"]
        # Check and deduct against the current database value in one statement.
        # Validation may have read stock before another request consumed it.
        updated = FeedStock.objects.filter(
            pk=stock.pk,
            farm=self.request.user.farm,
            quantity_kg__gte=quantity,
        ).update(
            quantity_kg=Round(F("quantity_kg") - quantity, precision=2),
            last_updated=timezone.now(),
        )
        if not updated:
            raise ValidationError({
                "quantity_kg": "Not enough feed stock remaining for this log entry.",
            })
        serializer.save(logged_by=self.request.user)
