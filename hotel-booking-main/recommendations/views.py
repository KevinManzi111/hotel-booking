from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from .forms import PreferenceForm
from .models import UserPreference, AIRecommendationQuery
from .services import (
    get_ai_concierge_recommendations,
    get_ai_engine_status,
    get_weights,
    recommendations_for,
)

SUGGESTED_AI_PROMPTS = [
    "Romantic suite with city views and breakfast",
    "Quiet workspace with high-speed Wi-Fi under $160",
    "Scenic escape with swimming pool and spa",
    "Family-friendly spacious suite in Kigali",
    "Best value boutique stay with ocean view",
]


@login_required
def preferences(request):
    preference, _ = UserPreference.objects.get_or_create(user=request.user)
    form = PreferenceForm(request.POST or None, instance=preference)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your travel preferences have been updated.")
        return redirect("recommendations:list")
    return render(request, "recommendations/preferences.html", {"form": form})


@login_required
def recommendation_list(request):
    preference, _ = UserPreference.objects.get_or_create(user=request.user)
    query = request.GET.get("q", "").strip() or request.POST.get("q", "").strip()
    mode = request.GET.get("mode", "ai").strip()

    ai_status = get_ai_engine_status()
    ai_summary = ""
    ai_hints = {}

    if mode == "classic" and not query:
        # Traditional deterministic rule-based matching
        results = recommendations_for(preference, use_ai=False)[:12]
        engine_label = "Classic Rule-Based Recommender"
    else:
        # Hybrid AI & Concierge matching
        concierge_data = get_ai_concierge_recommendations(
            query=query or getattr(preference, "ai_travel_vibe", ""),
            preference=preference,
            limit=12,
        )
        results = concierge_data["recommendations"]
        ai_summary = concierge_data["summary"]
        ai_hints = concierge_data["hints"]
        engine_label = concierge_data["engine"]

        # Log query history if a query was submitted
        if query:
            try:
                AIRecommendationQuery.objects.create(
                    user=request.user,
                    query_text=query,
                    parsed_intent={
                        "city": ai_hints.get("city"),
                        "room_type": ai_hints.get("room_type"),
                        "max_price": str(ai_hints.get("max_price")) if ai_hints.get("max_price") else None,
                        "vibes": ai_hints.get("vibes", []),
                        "amenities": list(ai_hints.get("amenities", [])),
                    },
                    result_count=len(results),
                )
            except Exception:
                pass

    context = {
        "recommendations": results,
        "weights": get_weights(),
        "preference": preference,
        "query": query,
        "mode": mode,
        "ai_status": ai_status,
        "ai_summary": ai_summary,
        "ai_hints": ai_hints,
        "engine_label": engine_label,
        "suggested_prompts": SUGGESTED_AI_PROMPTS,
    }
    return render(request, "recommendations/list.html", context)


@login_required
def ai_concierge_api(request):
    """
    JSON API for interactive real-time AI Travel Concierge queries.
    """
    query = request.GET.get("q", "").strip() or request.POST.get("q", "").strip()
    preference, _ = UserPreference.objects.get_or_create(user=request.user)

    concierge_data = get_ai_concierge_recommendations(
        query=query,
        preference=preference,
        limit=6,
    )

    items_data = []
    for item in concierge_data["recommendations"]:
        room = item["room"]
        items_data.append({
            "room_id": room.pk,
            "name": room.name,
            "room_type": room.get_room_type_display(),
            "hotel_name": room.hotel.name,
            "city": room.hotel.city,
            "country": room.hotel.country,
            "price": str(room.price_per_night),
            "score": item["score"],
            "confidence": item.get("confidence", "High"),
            "reasons": item.get("reasons", []),
            "concierge_note": item.get("ai_concierge_note", ""),
            "detail_url": reverse("hotels:room_detail", args=[room.pk]),
            "image_url": room.display_image or "",
        })

    return JsonResponse({
        "status": "success",
        "query": query,
        "engine": concierge_data["engine"],
        "summary": concierge_data["summary"],
        "hints": {
            "city": concierge_data["hints"].get("city"),
            "room_type": concierge_data["hints"].get("room_type"),
            "max_price": str(concierge_data["hints"].get("max_price")) if concierge_data["hints"].get("max_price") else None,
            "amenities": list(concierge_data["hints"].get("amenities", [])),
            "vibes": concierge_data["hints"].get("vibes", []),
        },
        "results": items_data,
    })
