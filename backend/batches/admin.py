from django.contrib import admin

from .models import ChickBatch


@admin.register(ChickBatch)
class ChickBatchAdmin(admin.ModelAdmin):
    list_display = ("batch_number", "farm", "shed", "arrival_date", "current_count", "status")
    list_filter = ("status", "farm")
    search_fields = ("batch_number",)
