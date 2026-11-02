from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from accounts.permissions import IsFarmOwnerOrEmployeeReadOnly

from .models import ChickBatch
from .serializers import ChickBatchSerializer


class ChickBatchListCreateView(generics.ListCreateAPIView):
    """Core Features: "Batch / Chick Management".
    GET: Owner and Employee both see every batch on their farm.
    POST: Owner only (registering a new flock batch is a decision, not a
    daily operational task)."""

    serializer_class = ChickBatchSerializer
    permission_classes = [IsFarmOwnerOrEmployeeReadOnly]

    def get_queryset(self):
        return ChickBatch.objects.filter(farm=self.request.user.farm).select_related("shed")

    def perform_create(self, serializer):
        if not self.request.user.is_owner:
            raise PermissionDenied("Only the farm owner can register a new batch.")
        serializer.save(
            farm=self.request.user.farm,
            created_by=self.request.user,
            current_count=serializer.validated_data["initial_count"],
        )


class ChickBatchDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChickBatchSerializer
    permission_classes = [IsFarmOwnerOrEmployeeReadOnly]

    def get_queryset(self):
        return ChickBatch.objects.filter(farm=self.request.user.farm)
