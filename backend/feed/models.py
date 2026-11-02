import uuid

from django.conf import settings
from django.db import models


class FeedStock(models.Model):
    """Current feed inventory for a farm (Core Features: "Feed & Inventory
    Management"). Employees log consumption against this; Owners/Employees
    can both see stock levels, only Owner/Admin can add new stock (restock)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="feed_stocks")
    feed_type = models.CharField(max_length=100)
    quantity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    reorder_threshold_kg = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("farm", "feed_type")

    def __str__(self):
        return f"{self.farm.name} — {self.feed_type} ({self.quantity_kg}kg)"

    @property
    def needs_reorder(self):
        return self.quantity_kg <= self.reorder_threshold_kg


class FeedConsumptionLog(models.Model):
    """Daily consumption entry. Employees create these as part of their
    day-to-day monitoring tasks; it decrements the related FeedStock."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey("batches.ChickBatch", on_delete=models.CASCADE, related_name="feed_logs")
    feed_stock = models.ForeignKey(FeedStock, on_delete=models.PROTECT, related_name="consumption_logs")
    quantity_kg = models.DecimalField(max_digits=8, decimal_places=2)
    log_date = models.DateField()
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-log_date"]

    def __str__(self):
        return f"{self.batch} — {self.quantity_kg}kg on {self.log_date}"
