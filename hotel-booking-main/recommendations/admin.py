from django.contrib import admin
from .models import UserPreference, AIRecommendationQuery


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "preferred_city", "preferred_room_type", "max_price", "guests", "ai_travel_vibe", "updated_at")


@admin.register(AIRecommendationQuery)
class AIRecommendationQueryAdmin(admin.ModelAdmin):
    list_display = ("user", "query_text", "result_count", "created_at")
    list_filter = ("created_at",)
    search_fields = ("query_text", "user__username")
