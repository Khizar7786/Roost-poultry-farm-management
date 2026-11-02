from django.contrib import admin

from .models import VaccinationRecord


@admin.register(VaccinationRecord)
class VaccinationRecordAdmin(admin.ModelAdmin):
    list_display = ("batch", "vaccine_name", "scheduled_date", "status", "administered_by")
    list_filter = ("status",)
