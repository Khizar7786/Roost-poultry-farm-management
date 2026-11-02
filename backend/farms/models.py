import uuid

from django.conf import settings
from django.db import models


class Farm(models.Model):
    """Created via UC-05 (Register Farm/Account). One Farm has exactly one
    Owner (the user who registered it) and zero or more Employees."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    location = models.CharField(max_length=255)
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_farm",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Shed(models.Model):
    """A physical shed/coop belonging to a farm. Batches live in a shed."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="sheds")
    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(help_text="Max number of birds this shed can hold.")

    class Meta:
        unique_together = ("farm", "name")

    def __str__(self):
        return f"{self.farm.name} — {self.name}"
