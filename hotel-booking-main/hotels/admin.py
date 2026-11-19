from django.contrib import admin
from .models import Amenity, Hotel, Room

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    search_fields = ("name",)

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "rating", "featured")
    list_filter = ("featured", "city")

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("identifier", "name", "hotel", "room_type", "bed_type", "view_type", "price_per_night", "has_breakfast", "has_ac", "is_quiet", "status")
    list_filter = ("status", "room_type", "bed_type", "view_type", "has_breakfast", "has_ac", "is_quiet", "hotel")
    search_fields = ("identifier", "name", "hotel__name")
    filter_horizontal = ("amenities",)
    readonly_fields = ("created_at", "updated_at")
