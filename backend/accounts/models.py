import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    """Stakeholders defined in the FYP documentation (Section 2.2 / 3.2).

    OWNER    -> "Farm Owner": monitors performance, makes decisions,
                 sees dashboard, reports, price predictions, manages employees.
    EMPLOYEE -> "Farm Employee": operates daily activities (image capture,
                 feed logging, vaccination administration). No financial /
                 sales visibility, no user management.
    ADMIN    -> "System Admin": manages system configuration & user access.
    """

    OWNER = "OWNER", "Farm Owner"
    EMPLOYEE = "EMPLOYEE", "Farm Employee"
    ADMIN = "ADMIN", "System Admin"


class User(AbstractUser):
    """Extends Django's built-in user with a role and a farm link.

    UC-04 (User Login) and UC-05 (Register Farm/Account) both operate on
    this model: registering a new farm creates a User with role=OWNER and
    a new Farm; an owner creating staff creates a User with role=EMPLOYEE
    attached to the owner's existing Farm.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.EMPLOYEE)
    phone_number = models.CharField(max_length=20, blank=True)

    # Nullable because a brand-new OWNER signup creates the User first and
    # the Farm in the same transaction (see accounts.serializers.RegisterFarmSerializer).
    farm = models.ForeignKey(
        "farms.Farm",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="members",
    )

    is_active_employee = models.BooleanField(
        default=True,
        help_text="Owners/Admins can deactivate an employee without deleting their account.",
    )

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_owner(self):
        return self.role == Role.OWNER

    @property
    def is_employee(self):
        return self.role == Role.EMPLOYEE

    @property
    def is_system_admin(self):
        return self.role == Role.ADMIN
