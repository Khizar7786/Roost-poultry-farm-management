import uuid

from django.conf import settings
from django.db import models


# ---------------------------------------------------------------------------
# UC-01 Chick Counting
# ---------------------------------------------------------------------------
class CountingSession(models.Model):
    """One chick-counting inference run. Primary actor per the docs is
    the Farmer/Employee capturing an image; the AI model is the
    secondary actor. `image` is what was captured, `count`/`confidence`/
    `boxes` are what the inference engine returned."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey("batches.ChickBatch", on_delete=models.CASCADE, related_name="counting_sessions")
    image = models.ImageField(upload_to="chick_counting/%Y/%m/%d/")
    count = models.PositiveIntegerField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    boxes = models.JSONField(default=list, blank=True, help_text="Bounding boxes returned by the inference engine.")
    model_version = models.CharField(max_length=50, blank=True)
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True)
    captured_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Count session {self.id} — batch {self.batch.batch_number}"


# ---------------------------------------------------------------------------
# UC-02 Mortality Detection
# ---------------------------------------------------------------------------
class MortalitySource(models.TextChoices):
    AI_DETECTED = "AI", "AI Detected"
    MANUAL = "MANUAL", "Manually Logged"


class MortalityEvent(models.Model):
    """Logged manually by an Employee/Owner (UC-02). `source` still
    distinguishes AI_DETECTED from MANUAL in case an automated detection
    pathway is added back later, but nothing currently creates AI-sourced
    rows — the behaviour-detection model that used to do that has been
    removed. Confirmed events decrement the batch's `current_count`
    (see monitoring/views.py)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey("batches.ChickBatch", on_delete=models.CASCADE, related_name="mortality_events")
    source = models.CharField(max_length=10, choices=MortalitySource.choices)
    detected_count = models.PositiveIntegerField(default=1)
    confidence = models.FloatField(null=True, blank=True)
    image = models.ImageField(upload_to="mortality/%Y/%m/%d/", null=True, blank=True)
    confirmed = models.BooleanField(
        default=False,
        help_text="Low-confidence AI detections wait for confirmation in the next frame (UC-02 alt. flow).",
    )
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Mortality x{self.detected_count} — {self.batch.batch_number} ({self.source})"


# ---------------------------------------------------------------------------
# UC-03 Market Price Prediction
# ---------------------------------------------------------------------------
class PricePrediction(models.Model):
    """One price-forecast run from the real trained LSTM+XGBoost hybrid
    model. Owner-only per the capability split (it's a planning/decision
    tool, not a daily task). The model forecasts the Lahore farm-gate
    market price from its own embedded historical dataset — not derived
    from this particular farm's sales records."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="price_predictions")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    horizon_days = models.PositiveSmallIntegerField(default=10)
    forecast = models.JSONField(
        default=list,
        help_text="[{day, date, price_pkr, delta_pkr, delta_pct, direction, prob_up, prob_down, "
                  "confidence, low_confidence, rsi14, macd_hist, events}, ...]",
    )
    summary = models.JSONField(
        default=dict,
        help_text="{up_days, down_days, uncertain_days, final_price_pkr, net_change_pkr, net_change_pct}",
    )
    last_known_date = models.CharField(max_length=10, blank=True)
    last_known_price_pkr = models.FloatField(null=True, blank=True)
    model_accuracy = models.FloatField(null=True, blank=True, help_text="Held-out test accuracy of the direction classifier.")
    confidence_threshold = models.FloatField(null=True, blank=True)
    model_version = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Forecast for {self.farm.name} ({self.horizon_days}d) @ {self.created_at:%Y-%m-%d}"
