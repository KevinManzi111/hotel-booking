"""
Recommendation services for Staywise.

Provides deterministic explainable weighted matching as well as
the new Hybrid AI & LLM Concierge recommendation system.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from django.conf import settings
from hotels.models import Room
from .ai_concierge import AIConcierge
from .ai_engine import HybridRoomRecommender

DEFAULT_WEIGHTS = {"budget": .30, "location": .20, "room_type": .20, "amenities": .20, "capacity": .10}


def get_weights():
    configured = getattr(settings, "RECOMMENDATION_WEIGHTS", DEFAULT_WEIGHTS)
    weights = {key: max(float(configured.get(key, 0)), 0) for key in DEFAULT_WEIGHTS}
    total = sum(weights.values())
    if total <= 0:
        return DEFAULT_WEIGHTS.copy()
    return {key: value / total for key, value in weights.items()}


def get_ai_engine_status() -> Dict[str, Any]:
    """Inspect current AI engine configuration and status."""
    gemini_key = bool(getattr(settings, "GEMINI_API_KEY", ""))
    openai_key = bool(getattr(settings, "OPENAI_API_KEY", ""))
    if gemini_key:
        active_label = "Google Gemini AI + Hybrid ML"
        mode = "gemini"
    elif openai_key:
        active_label = "OpenAI GPT-4o-mini + Hybrid ML"
        mode = "openai"
    else:
        active_label = "Hybrid ML Engine (Offline Smart Fallback)"
        mode = "offline_ml"

    return {
        "label": active_label,
        "mode": mode,
        "gemini_connected": gemini_key,
        "openai_connected": openai_key,
        "offline_ready": True,
    }


def _budget_score(price, maximum):
    """1 within budget; linear decline to 0 at 150% of budget."""
    if maximum in (None, ""):
        return .5
    price, maximum = Decimal(price), Decimal(maximum)
    if maximum <= 0:
        return 0.0
    if price <= maximum:
        return 1.0
    return max(0.0, 1.0 - float((price - maximum) / (maximum * Decimal("0.5"))))


def is_available(room, check_in=None, check_out=None):
    if room.status != "available":
        return False
    if not check_in or not check_out:
        return True
    return not room.bookings.filter(status="confirmed", check_in__lt=check_out, check_out__gt=check_in).exists()


def score_room(room, preference, weights=None):
    weights = weights or get_weights()
    wanted = set(preference.amenities.values_list("id", flat=True)) if hasattr(preference, "amenities") else set()
    offered = set(room.amenities.values_list("id", flat=True)) | set(room.hotel.amenities.values_list("id", flat=True))
    matched = wanted & offered
    raw = {
        "budget": _budget_score(room.price_per_night, getattr(preference, "max_price", None)),
        "location": 1.0 if getattr(preference, "preferred_city", "") and preference.preferred_city.casefold() in f"{room.hotel.city} {room.hotel.country}".casefold() else (.5 if not getattr(preference, "preferred_city", "") else 0.0),
        "room_type": 1.0 if getattr(preference, "preferred_room_type", "") and room.room_type == preference.preferred_room_type else (.5 if not getattr(preference, "preferred_room_type", "") else 0.0),
        "amenities": len(matched) / len(wanted) if wanted else .5,
        "capacity": min(1.0, room.capacity / max(getattr(preference, "guests", 1), 1)),
    }
    contributions = {key: round(raw[key] * weights[key] * 100, 1) for key in weights}
    reasons = []
    if raw["budget"] == 1:
        reasons.append("Within your nightly budget")
    elif getattr(preference, "max_price", None) and raw["budget"] > 0:
        reasons.append("Slightly above budget, with other strong matches")
    if raw["location"] == 1:
        reasons.append(f"In your preferred destination, {room.hotel.city}")
    if raw["room_type"] == 1:
        reasons.append(f"Your preferred {room.get_room_type_display().lower()} room type")
    if matched:
        reasons.append(f"Matches {len(matched)} of {len(wanted)} selected amenities")
    reasons.append(f"Fits your group of {getattr(preference, 'guests', 2)}")
    if getattr(preference, "requested_check_in", None):
        reasons.append("Available for your requested dates")
    optional_empty = not any([getattr(preference, "preferred_city", ""), getattr(preference, "preferred_room_type", ""), getattr(preference, "max_price", None), wanted])
    if optional_empty:
        reasons = ["Meets your guest capacity", "Ranked consistently by price when preferences are open"]
    return {
        "room": room,
        "score": round(sum(contributions.values()), 1),
        "reasons": reasons[:4],
        "breakdown": {key: {"raw": round(raw[key] * 100), "weight": round(weights[key] * 100), "points": contributions[key]} for key in weights}
    }


def eligible_rooms(preference, queryset=None):
    rooms = queryset if queryset is not None else Room.objects.all()
    guests = max(getattr(preference, "guests", 1), 1) if preference else 1
    rooms = rooms.filter(status="available", capacity__gte=guests).select_related("hotel").prefetch_related("amenities", "hotel__amenities")
    if preference and getattr(preference, "requested_check_in", None) and getattr(preference, "requested_check_out", None):
        rooms = rooms.exclude(bookings__status="confirmed", bookings__check_in__lt=preference.requested_check_out, bookings__check_out__gt=preference.requested_check_in)
    return rooms.distinct()


def recommendations_for(preference, queryset=None, use_ai=False):
    """
    Standard room recommendations for a user preference profile.
    If use_ai=True, utilizes the Hybrid ML recommender.
    """
    eligible = eligible_rooms(preference, queryset)
    if use_ai:
        ml = HybridRoomRecommender()
        return ml.rank_rooms(list(eligible), preference=preference, natural_query=getattr(preference, "ai_travel_vibe", ""))
    results = [score_room(room, preference) for room in eligible]
    return sorted(results, key=lambda item: (-item["score"], Decimal(str(item["room"].price_per_night)), item["room"].pk))


def recommendation_for_room(room, preference):
    if room.capacity < getattr(preference, "guests", 1) or not is_available(room, getattr(preference, "requested_check_in", None), getattr(preference, "requested_check_out", None)):
        return None
    return score_room(room, preference)


def get_ai_concierge_recommendations(
    query: Optional[str] = None,
    preference: Optional[Any] = None,
    check_in: Optional[Any] = None,
    check_out: Optional[Any] = None,
    guests: Optional[int] = None,
    limit: int = 12,
) -> Dict[str, Any]:
    """
    High-level entry point for AI Travel Concierge recommendations.
    Accepts natural language queries, user preferences, and travel dates.
    """
    concierge = AIConcierge()
    return concierge.recommend(
        query=query,
        preference=preference,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        limit=limit,
    )


def evaluate_profiles(preferences, queryset=None, limit=3, use_ai=False):
    """Offline evaluation: coverage and top-k output for sample profiles."""
    profiles, returned_ids = [], set()
    available_count = (queryset if queryset is not None else Room.objects.filter(status="available")).count()
    for preference in preferences:
        ranked = recommendations_for(preference, queryset, use_ai=use_ai)[:limit]
        ids = [item["room"].pk for item in ranked]
        returned_ids.update(ids)
        profiles.append({
            "user": getattr(preference, "user_id", "anon"),
            "count": len(ranked),
            "top_room_ids": ids,
            "top_scores": [item["score"] for item in ranked],
        })
    return {
        "profiles": profiles,
        "catalogue_coverage": round(len(returned_ids) / available_count, 3) if available_count else 0.0,
        "profiles_evaluated": len(profiles),
        "engine": "hybrid_ai" if use_ai else "deterministic",
    }
