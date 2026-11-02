from django.contrib import admin

from .models import FeedConsumptionLog, FeedStock


@admin.register(FeedStock)
class FeedStockAdmin(admin.ModelAdmin):
    list_display = ("farm", "feed_type", "quantity_kg", "reorder_threshold_kg")
    list_filter = ("farm",)


@admin.register(FeedConsumptionLog)
class FeedConsumptionLogAdmin(admin.ModelAdmin):
    list_display = ("batch", "feed_stock", "quantity_kg", "log_date", "logged_by")
    list_filter = ("log_date",)
