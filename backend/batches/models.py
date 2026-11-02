import uuid

from django.conf import settings
from django.db import models


class BatchStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    SOLD = "SOLD", "Sold / Closed"
    CULLED = "CULLED", "Culled"


class ChickBatch(models.Model):
    """A tracked flock batch (Web System — Core Features: "Batch / Chick
    Management"). AI results (chick counts, mortality events)
    and operational logs (feed, vaccination) all attach to a batch."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="batches")
    shed = models.ForeignKey("farms.Shed", on_delete=models.SET_NULL, null=True, related_name="batches")
    batch_number = models.CharField(max_length=50)
    arrival_date = models.DateField()
    initial_count = models.PositiveIntegerField()
    current_count = models.PositiveIntegerField(
        help_text="Kept in sync as mortality events / recounts are recorded."
    )
    status = models.CharField(max_length=10, choices=BatchStatus.choices, default=BatchStatus.ACTIVE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("farm", "batch_number")
        ordering = ["-arrival_date"]

    def __str__(self):
        return f"{self.farm.name} / Batch {self.batch_number}"

    @property
    def age_days(self):
        from django.utils import timezone

        return (timezone.now().date() - self.arrival_date).days

    @property
    def mortality_count(self):
        return self.initial_count - self.current_count

    @property
    def mortality_rate_pct(self):
        if self.initial_count == 0:
            return 0.0
        return round((self.mortality_count / self.initial_count) * 100, 2)
