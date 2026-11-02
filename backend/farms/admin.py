from django.contrib import admin

from .models import Farm, Shed


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "owner", "created_at")
    search_fields = ("name", "owner__username")


@admin.register(Shed)
class ShedAdmin(admin.ModelAdmin):
    list_display = ("name", "farm", "capacity")
    list_filter = ("farm",)
