"""
Shared permission classes encoding the stakeholder capability split from
the FYP documentation (Section 2.2 Stakeholders, 2.3 Affected Groups):

  Farm Owner    -> monitors performance, makes decisions: full read/write
                   on their own farm's data, manages employees, sees sales
                   & price predictions.
  Farm Employee -> operates daily activities: can capture images for AI
                   inference, log feed/vaccination, view (not edit)
                   batches — but no sales, no user management, no price
                   prediction requests.
  System Admin  -> manages system configuration & user access, not farm
                   operational data.

Every object below is farm-scoped: a user may only touch rows belonging
to `request.user.farm`.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_system_admin)


class IsFarmOwner(BasePermission):
    """Full access, scoped to the owner's own farm."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_owner)

    def has_object_permission(self, request, view, obj):
        farm = _extract_farm(obj)
        return farm is not None and farm_id_matches(request.user, farm)


class IsFarmOwnerOrEmployeeReadOnly(BasePermission):
    """Owners get full CRUD; Employees get read-only. Both are restricted
    to their own farm's data."""

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_owner or user.is_system_admin:
            return True
        return user.is_employee and request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        user = request.user
        farm = _extract_farm(obj)
        if farm is None or not farm_id_matches(user, farm):
            return False
        if user.is_owner or user.is_system_admin:
            return True
        return request.method in SAFE_METHODS


class IsFarmMember(BasePermission):
    """Owner or Employee of the same farm, any HTTP method — used for
    endpoints Employees are explicitly allowed to write to (image capture,
    feed logs, marking vaccinations administered, acknowledging alerts)."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.farm_id and not user.is_system_admin)

    def has_object_permission(self, request, view, obj):
        farm = _extract_farm(obj)
        return farm is not None and farm_id_matches(request.user, farm)


def _extract_farm(obj):
    """Most models are farm-scoped directly (`obj.farm`) or transitively
    through a batch (`obj.batch.farm`)."""
    if hasattr(obj, "farm_id"):
        return obj.farm
    if hasattr(obj, "batch") and obj.batch is not None:
        return obj.batch.farm
    return None


def farm_id_matches(user, farm) -> bool:
    return user.farm_id is not None and str(user.farm_id) == str(farm.id)
