from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsFarmMember

from .models import Alert, AlertSeverity
from .serializers import AlertSerializer


class AlertListView(generics.ListAPIView):
    """Both Owner and Employee see alerts for their farm — mortality,
    feed, and vaccination alerts are everyone's business on the ground,
    financial reports are not (see sales app for the owner-only split)."""

    serializer_class = AlertSerializer
    permission_classes = [IsFarmMember]

    def get_queryset(self):
        qs = Alert.objects.filter(farm=self.request.user.farm)
        unacknowledged_only = self.request.query_params.get("unacknowledged") == "true"
        if unacknowledged_only:
            qs = qs.filter(acknowledged=False)
        return qs


class AcknowledgeAlertView(APIView):
    permission_classes = [IsFarmMember]

    def post(self, request, pk):
        alert = Alert.objects.filter(pk=pk, farm=request.user.farm).first()
        if not alert:
            return Response({"detail": "Not found."}, status=404)
        alert.acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save(update_fields=["acknowledged", "acknowledged_by", "acknowledged_at"])
        return Response(AlertSerializer(alert).data)


class EscalateOverdueAlertsView(APIView):
    """UC-08 alt. flow: unacknowledged HIGH-priority alert past its window
    gets escalated (e.g. SMS to a secondary contact). Intended to be hit
    by a periodic task (cron / Celery beat) rather than a user."""

    permission_classes = [IsFarmMember]

    def post(self, request):
        candidates = Alert.objects.filter(
            farm=request.user.farm, severity=AlertSeverity.HIGH, acknowledged=False, escalated=False
        )
        escalated = [a for a in candidates if a.is_overdue_for_escalation]
        for alert in escalated:
            alert.escalated = True
        Alert.objects.bulk_update(escalated, ["escalated"])
        return Response({"escalated_count": len(escalated), "alerts": AlertSerializer(escalated, many=True).data})
