from django.contrib import admin

from .models import SaleRecord


@admin.register(SaleRecord)
class SaleRecordAdmin(admin.ModelAdmin):
    list_display = ("farm", "buyer_name", "quantity", "price_per_unit", "sale_date")
    list_filter = ("farm",)
