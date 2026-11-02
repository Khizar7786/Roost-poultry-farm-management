from django.db import transaction
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsFarmMember, IsFarmOwner
from ai_integration.engine import AIServiceError, count_chicks, predict_price
from alerts.models import Alert, AlertSeverity, AlertType

from .models import CountingSession, MortalityEvent, PricePrediction
from .serializers import (
    CountingSessionSerializer,
    MortalityEventSerializer,
    PricePredictionRequestSerializer,
    PricePredictionSerializer,
)


# ---------------------------------------------------------------------------
# UC-01 Chick Counting
# ---------------------------------------------------------------------------
class CountingSessionListCreateView(generics.ListCreateAPIView):
    """Farmer/Employee captures or uploads an image; this view forwards it
    to the local chick-counting inference engine and stores the result."""

    serializer_class = CountingSessionSerializer
    permission_classes = [IsFarmMember]

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        return CountingSession.objects.filter(batch__farm=self.request.user.farm).select_related("batch")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = serializer.save(captured_by=request.user)

        try:
            result = count_chicks(session.image)
        except AIServiceError as exc:
            # UC-01 alt. flow (poor image quality) is reported by the AI
            # service itself as a 4xx; anything else is a service outage.
            session.delete()
            return Response({"detail": str(exc)}, status=exc.status_code)

        session.count = result.get("count")
        session.confidence = result.get("confidence")
        session.boxes = result.get("boxes", [])
        session.model_version = result.get("model_version", "")
        session.processing_time_ms = result.get("processing_time_ms")
        session.save()
        return Response(self.get_serializer(session).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# UC-02 Mortality Detection — manual logging only. There is no AI-detection
# pathway anymore (that used to come from the behaviour-detection model,
# which has been removed); `MortalityEvent.source` stays MANUAL for every
# row created here.
# ---------------------------------------------------------------------------
class MortalityEventListCreateView(generics.ListCreateAPIView):
    serializer_class = MortalityEventSerializer
    permission_classes = [IsFarmMember]

    def get_serializer_context(self):
        return {"request": self.request}

    def get_queryset(self):
        return MortalityEvent.objects.filter(batch__farm=self.request.user.farm).select_related("batch")

    @transaction.atomic
    def perform_create(self, serializer):
        event = serializer.save(logged_by=self.request.user)
        _apply_mortality_to_batch(event)
        Alert.objects.create(
            farm=event.batch.farm,
            batch=event.batch,
            alert_type=AlertType.MORTALITY,
            severity=AlertSeverity.HIGH,
            message=f"{event.detected_count} mortality event(s) logged for batch {event.batch.batch_number}.",
        )


# ---------------------------------------------------------------------------
# UC-03 Market Price Prediction — Owner-only planning tool
# ---------------------------------------------------------------------------
class PricePredictionListView(generics.ListAPIView):
    serializer_class = PricePredictionSerializer
    permission_classes = [IsFarmOwner]

    def get_queryset(self):
        return PricePrediction.objects.filter(farm=self.request.user.farm)


class TriggerPricePredictionView(APIView):
    """UC-03 main flow: farmer selects prediction -> AI model analyzes
    -> result displayed. The trained model carries its own historical
    market dataset (Lahore farm-gate broiler prices), so this no longer
    depends on the farm's own sales records — a market-level forecast
    isn't really about any one farm's transaction history."""

    permission_classes = [IsFarmOwner]

    def post(self, request):
        if not request.user.is_owner:
            raise PermissionDenied("Only the farm owner can request a price forecast.")

        req = PricePredictionRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        horizon_days = req.validated_data["horizon_days"]

        try:
            result = predict_price(horizon_days)
        except AIServiceError as exc:
            return Response({"detail": str(exc)}, status=exc.status_code)

        prediction = PricePrediction.objects.create(
            farm=request.user.farm,
            requested_by=request.user,
            horizon_days=horizon_days,
            forecast=result.get("forecast", []),
            summary=result.get("summary", {}),
            last_known_date=result.get("last_known_date"),
            last_known_price_pkr=result.get("last_known_price_pkr"),
            model_accuracy=result.get("model_accuracy"),
            confidence_threshold=result.get("confidence_threshold"),
            model_version="broiler-lstm28-xgboost-v1",
        )
        return Response(PricePredictionSerializer(prediction).data, status=status.HTTP_201_CREATED)


def _apply_mortality_to_batch(event: MortalityEvent):
    batch = event.batch
    batch.current_count = max(0, batch.current_count - event.detected_count)
    batch.save(update_fields=["current_count"])
