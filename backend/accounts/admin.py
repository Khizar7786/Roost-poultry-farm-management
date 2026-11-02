from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "farm", "is_active_employee", "is_active")
    list_filter = ("role", "is_active_employee", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Farm role", {"fields": ("role", "farm", "phone_number", "is_active_employee")}),
    )
