from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from alerts.models import Alert
from alerts.serializers import AlertSerializer
from batches.models import BatchStatus, ChickBatch
from feed.models import FeedStock
from health.models import VaccinationRecord, VaccinationStatus
from monitoring.models import CountingSession, MortalityEvent, PricePrediction


class DashboardView(APIView):
    """UC-07: farmer logs in -> redirected to dashboard -> system
    aggregates counting/mortality/market data into one view.

    Owners get the full picture (including price forecasts and farm-wide
    totals); Employees get an operational subset — no financial data,
    consistent with the stakeholder capability split used throughout the
    rest of the API.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        farm = user.farm
        if not farm:
            return Response({"detail": "You are not attached to a farm yet."}, status=404)

        active_batches = ChickBatch.objects.filter(farm=farm, status=BatchStatus.ACTIVE)
        week_ago = timezone.now() - timedelta(days=7)

        flock_overview = {
            "active_batch_count": active_batches.count(),
            "total_birds": active_batches.aggregate(total=Sum("current_count"))["total"] or 0,
            "mortality_last_7_days": MortalityEvent.objects.filter(
                batch__farm=farm, confirmed=True, created_at__gte=week_ago
            ).count(),
            "recent_counting_sessions": _no_data_placeholder(
                CountingSession.objects.filter(batch__farm=farm).order_by("-created_at")[:5],
                lambda qs: [
                    {"batch": s.batch.batch_number, "count": s.count, "confidence": s.confidence,
                     "created_at": s.created_at}
                    for s in qs
                ],
            ),
        }

        unacknowledged_alerts = Alert.objects.filter(farm=farm, acknowledged=False)[:10]

        feed_warnings = [
            {"feed_type": f.feed_type, "quantity_kg": float(f.quantity_kg)}
            for f in FeedStock.objects.filter(farm=farm) if f.needs_reorder
        ]

        upcoming_vaccinations = VaccinationRecord.objects.filter(
            batch__farm=farm, status=VaccinationStatus.SCHEDULED, scheduled_date__gte=timezone.now().date()
        ).order_by("scheduled_date")[:5]

        payload = {
            "role": user.role,
            "farm_name": farm.name,
            "flock_overview": flock_overview,
            "alerts": AlertSerializer(unacknowledged_alerts, many=True).data,
            "feed_stock_warnings": feed_warnings or "No feed stock warnings.",
            "upcoming_vaccinations": _no_data_placeholder(
                upcoming_vaccinations,
                lambda qs: [
                    {"batch": v.batch.batch_number, "vaccine": v.vaccine_name, "scheduled_date": v.scheduled_date}
                    for v in qs
                ],
            ),
        }

        # Owner-only widgets: latest market price forecast + a note if
        # there is none yet (UC-07 alt. flow: "no data" placeholder).
        if user.is_owner:
            latest_forecast = PricePrediction.objects.filter(farm=farm).order_by("-created_at").first()
            payload["market_price_forecast"] = (
                {
                    "created_at": latest_forecast.created_at,
                    "horizon_days": latest_forecast.horizon_days,
                    "forecast": latest_forecast.forecast,
                }
                if latest_forecast
                else "No price forecast has been generated yet."
            )

        return Response(payload)


def _no_data_placeholder(queryset, transform):
    items = list(queryset)
    if not items:
        return "No data available."
    return transform(items)
