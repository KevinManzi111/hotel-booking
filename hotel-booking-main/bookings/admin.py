from django.contrib import admin
from .models import Booking
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "room", "check_in", "check_out", "status", "total_price")
    list_filter = ("status", "check_in"); search_fields = ("user__username", "room__name", "room__hotel__name")
    readonly_fields = ("reference", "total_price", "created_at", "updated_at")
