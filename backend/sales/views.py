from rest_framework import generics

from accounts.permissions import IsFarmOwner

from .models import SaleRecord
from .serializers import SaleRecordSerializer


class SaleRecordListCreateView(generics.ListCreateAPIView):
    """Core Features: "Sales & Reports" — financial data, Farm Owner only.
    Employees get a 403 here (see IsFarmOwner + Section 2.2 stakeholder
    table: only the Owner "monitors farm performance and makes decisions")."""

    serializer_class = SaleRecordSerializer
    permission_classes = [IsFarmOwner]

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        return SaleRecord.objects.filter(farm=self.request.user.farm).select_related("batch")

    def perform_create(self, serializer):
        serializer.save(farm=self.request.user.farm, recorded_by=self.request.user)


class SaleRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SaleRecordSerializer
    permission_classes = [IsFarmOwner]

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        return SaleRecord.objects.filter(farm=self.request.user.farm)
