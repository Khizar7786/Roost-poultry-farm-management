from django.contrib import admin

from .models import CountingSession, MortalityEvent, PricePrediction


@admin.register(CountingSession)
class CountingSessionAdmin(admin.ModelAdmin):
    list_display = ("batch", "count", "confidence", "created_at")
    list_filter = ("batch__farm",)


@admin.register(MortalityEvent)
class MortalityEventAdmin(admin.ModelAdmin):
    list_display = ("batch", "source", "detected_count", "confirmed", "created_at")
    list_filter = ("source", "confirmed")


@admin.register(PricePrediction)
class PricePredictionAdmin(admin.ModelAdmin):
    list_display = ("farm", "horizon_days", "created_at")
