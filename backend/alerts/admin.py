from django.contrib import admin

from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ("farm", "alert_type", "severity", "message", "acknowledged", "escalated", "created_at")
    list_filter = ("severity", "alert_type", "acknowledged", "escalated")
