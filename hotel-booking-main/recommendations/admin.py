from django.contrib import admin
from .models import UserPreference
@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin): list_display = ("user", "preferred_city", "preferred_room_type", "max_price", "guests", "updated_at")
