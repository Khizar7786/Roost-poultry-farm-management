import uuid

from django.conf import settings
from django.db import models


class AlertSeverity(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"


class AlertType(models.TextChoices):
    MORTALITY = "MORTALITY", "Mortality Detected"
    FEED_LOW = "FEED_LOW", "Feed Stock Low"
    VACCINATION_DUE = "VACCINATION_DUE", "Vaccination Due"
    SYSTEM = "SYSTEM", "System Error"


class Alert(models.Model):
    """UC-08 Alerts. Created by other apps' view logic (mortality events,
    low feed stock, due vaccinations) — never created directly by a user.
    Farmer/Owner can acknowledge; unacknowledged HIGH severity alerts past
    `escalate_after_minutes` get escalated."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="alerts")
    batch = models.ForeignKey(
        "batches.ChickBatch", on_delete=models.CASCADE, related_name="alerts", null=True, blank=True
    )
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    severity = models.CharField(max_length=10, choices=AlertSeverity.choices, default=AlertSeverity.MEDIUM)
    message = models.CharField(max_length=255)

    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    escalated = models.BooleanField(default=False)
    escalate_after_minutes = models.PositiveIntegerField(default=30)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.severity}] {self.message}"

    @property
    def is_overdue_for_escalation(self):
        from django.utils import timezone

        if self.acknowledged or self.escalated or self.severity != AlertSeverity.HIGH:
            return False
        age_minutes = (timezone.now() - self.created_at).total_seconds() / 60
        return age_minutes >= self.escalate_after_minutes
