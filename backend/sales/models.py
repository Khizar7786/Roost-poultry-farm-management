import uuid

from django.conf import settings
from django.db import models


class SaleRecord(models.Model):
    """Core Features: "Sales & Reports". Financial data — visible to the
    Farm Owner (and System Admin) only; Employees have no access per the
    stakeholder capability split in the documentation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="sales")
    batch = models.ForeignKey("batches.ChickBatch", on_delete=models.SET_NULL, null=True, related_name="sales")
    buyer_name = models.CharField(max_length=150)
    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sale_date"]

    def __str__(self):
        return f"{self.farm.name} sale to {self.buyer_name} on {self.sale_date}"

    @property
    def total_amount(self):
        return self.quantity * self.price_per_unit
