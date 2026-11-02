import uuid

from django.conf import settings
from django.db import models


class VaccinationStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    ADMINISTERED = "ADMINISTERED", "Administered"
    MISSED = "MISSED", "Missed"


class VaccinationRecord(models.Model):
    """Core Features: "Vaccination & Mortality Records". Owners (or Admins)
    schedule vaccinations; Employees carry them out and mark them
    administered — this mirrors the Owner="decisions" / Employee="daily
    operations" split from the stakeholder table."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey("batches.ChickBatch", on_delete=models.CASCADE, related_name="vaccinations")
    vaccine_name = models.CharField(max_length=150)
    scheduled_date = models.DateField()
    administered_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=VaccinationStatus.choices, default=VaccinationStatus.SCHEDULED)
    scheduled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="vaccinations_scheduled"
    )
    administered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="vaccinations_administered",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["scheduled_date"]

    def __str__(self):
        return f"{self.batch} — {self.vaccine_name} ({self.status})"
