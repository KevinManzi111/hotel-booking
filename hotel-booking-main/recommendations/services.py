"""Deterministic, explainable weighted content-based room matching."""
from decimal import Decimal
from django.conf import settings
from hotels.models import Room

DEFAULT_WEIGHTS = {"budget": .30, "location": .20, "room_type": .20, "amenities": .20, "capacity": .10}

def get_weights():
    configured = getattr(settings, "RECOMMENDATION_WEIGHTS", DEFAULT_WEIGHTS)
    weights = {key: max(float(configured.get(key, 0)), 0) for key in DEFAULT_WEIGHTS}
    total = sum(weights.values())
    if total <= 0: return DEFAULT_WEIGHTS.copy()
    return {key: value / total for key, value in weights.items()}

def _budget_score(price, maximum):
    """1 within budget; linear decline to 0 at 150% of budget."""
    if maximum in (None, ""): return .5
    price, maximum = Decimal(price), Decimal(maximum)
    if maximum <= 0: return 0.0
    if price <= maximum: return 1.0
    return max(0.0, 1.0 - float((price - maximum) / (maximum * Decimal("0.5"))))

def is_available(room, check_in=None, check_out=None):
    if room.status != "available": return False
    if not check_in or not check_out: return True
    return not room.bookings.filter(status="confirmed", check_in__lt=check_out, check_out__gt=check_in).exists()

def score_room(room, preference, weights=None):
    weights = weights or get_weights()
    wanted = set(preference.amenities.values_list("id", flat=True))
    offered = set(room.amenities.values_list("id", flat=True)) | set(room.hotel.amenities.values_list("id", flat=True))
    matched = wanted & offered
    raw = {
        "budget": _budget_score(room.price_per_night, preference.max_price),
        "location": 1.0 if preference.preferred_city and preference.preferred_city.casefold() in f"{room.hotel.city} {room.hotel.country}".casefold() else (.5 if not preference.preferred_city else 0.0),
        "room_type": 1.0 if preference.preferred_room_type and room.room_type == preference.preferred_room_type else (.5 if not preference.preferred_room_type else 0.0),
        "amenities": len(matched) / len(wanted) if wanted else .5,
        "capacity": min(1.0, room.capacity / max(preference.guests, 1)),
    }
    contributions = {key: round(raw[key] * weights[key] * 100, 1) for key in weights}
    reasons = []
    if raw["budget"] == 1: reasons.append("Within your nightly budget")
    elif preference.max_price and raw["budget"] > 0: reasons.append("Slightly above budget, with other strong matches")
    if raw["location"] == 1: reasons.append(f"In your preferred destination, {room.hotel.city}")
    if raw["room_type"] == 1: reasons.append(f"Your preferred {room.get_room_type_display().lower()} room type")
    if matched: reasons.append(f"Matches {len(matched)} of {len(wanted)} selected amenities")
    reasons.append(f"Fits your group of {preference.guests}")
    if preference.requested_check_in: reasons.append("Available for your requested dates")
    optional_empty = not any([preference.preferred_city, preference.preferred_room_type, preference.max_price, wanted])
    if optional_empty: reasons = ["Meets your guest capacity", "Ranked consistently by price when preferences are open"]
    return {"room": room, "score": round(sum(contributions.values()), 1), "reasons": reasons[:4], "breakdown": {key: {"raw": round(raw[key] * 100), "weight": round(weights[key] * 100), "points": contributions[key]} for key in weights}}

def eligible_rooms(preference, queryset=None):
    rooms = queryset if queryset is not None else Room.objects.all()
    rooms = rooms.filter(status="available", capacity__gte=max(preference.guests, 1)).select_related("hotel").prefetch_related("amenities", "hotel__amenities")
    if preference.requested_check_in and preference.requested_check_out:
        rooms = rooms.exclude(bookings__status="confirmed", bookings__check_in__lt=preference.requested_check_out, bookings__check_out__gt=preference.requested_check_in)
    return rooms.distinct()

def recommendations_for(preference, queryset=None):
    results = [score_room(room, preference) for room in eligible_rooms(preference, queryset)]
    return sorted(results, key=lambda item: (-item["score"], Decimal(item["room"].price_per_night), item["room"].pk))

def recommendation_for_room(room, preference):
    if room.capacity < preference.guests or not is_available(room, preference.requested_check_in, preference.requested_check_out): return None
    return score_room(room, preference)

def evaluate_profiles(preferences, queryset=None, limit=3):
    """Small offline evaluation: coverage and top-k output for sample profiles."""
    profiles, returned_ids = [], set()
    available_count = (queryset if queryset is not None else Room.objects.filter(status="available")).count()
    for preference in preferences:
        ranked = recommendations_for(preference, queryset)[:limit]
        ids = [item["room"].pk for item in ranked]; returned_ids.update(ids)
        profiles.append({"user": preference.user_id, "count": len(ranked), "top_room_ids": ids, "top_scores": [item["score"] for item in ranked]})
    return {"profiles": profiles, "catalogue_coverage": round(len(returned_ids) / available_count, 3) if available_count else 0.0, "profiles_evaluated": len(profiles)}
