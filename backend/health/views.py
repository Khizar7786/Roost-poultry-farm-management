from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsFarmMember, IsFarmOwnerOrEmployeeReadOnly

from .models import VaccinationRecord, VaccinationStatus
from .serializers import VaccinationRecordSerializer


class VaccinationListCreateView(generics.ListCreateAPIView):
    """GET: Owner + Employee both see the vaccination schedule.
    POST (schedule a new vaccination): Owner only — this is a health-plan
    decision, not a daily task."""

    serializer_class = VaccinationRecordSerializer
    permission_classes = [IsFarmOwnerOrEmployeeReadOnly]

    def get_queryset(self):
        return VaccinationRecord.objects.filter(batch__farm=self.request.user.farm).select_related("batch")

    def perform_create(self, serializer):
        if not self.request.user.is_owner:
            raise PermissionDenied("Only the farm owner can schedule vaccinations.")
        serializer.save(scheduled_by=self.request.user)


class MarkAdministeredView(APIView):
    """Employee (or Owner) marks a scheduled vaccination as carried out —
    the actual "operates daily activities" step."""

    permission_classes = [IsFarmMember]

    def post(self, request, pk):
        record = VaccinationRecord.objects.filter(pk=pk, batch__farm=request.user.farm).first()
        if not record:
            return Response({"detail": "Not found."}, status=404)
        record.status = VaccinationStatus.ADMINISTERED
        record.administered_date = timezone.now().date()
        record.administered_by = request.user
        record.save(update_fields=["status", "administered_date", "administered_by"])
        return Response(VaccinationRecordSerializer(record).data)
