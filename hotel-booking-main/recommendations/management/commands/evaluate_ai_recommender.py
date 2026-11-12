import json
from types import SimpleNamespace
from django.core.management.base import BaseCommand
from hotels.models import Room
from recommendations.models import UserPreference
from recommendations.services import evaluate_profiles, get_ai_concierge_recommendations, get_ai_engine_status


class Command(BaseCommand):
    help = "Compare and evaluate Hybrid AI Recommender against classic deterministic baseline"

    def handle(self, *args, **options):
        profiles = list(UserPreference.objects.select_related("user").prefetch_related("amenities"))
        source = "saved"
        if not profiles:
            source = "synthetic"
            class EmptyAmenities:
                def all(self): return []
                def values_list(self, *args, **kwargs): return []
            rooms = list(Room.objects.filter(status="available").select_related("hotel")[:3])
            profiles = [
                SimpleNamespace(
                    user_id=f"sample-{i+1}",
                    preferred_city=room.hotel.city,
                    preferred_room_type=room.room_type,
                    max_price=room.price_per_night,
                    guests=min(room.capacity, 2),
                    requested_check_in=None,
                    requested_check_out=None,
                    ai_travel_vibe="romantic relaxing escape",
                    amenities=EmptyAmenities()
                )
                for i, room in enumerate(rooms)
            ]

        # 1. Evaluate classic deterministic
        classic_report = evaluate_profiles(profiles, use_ai=False)
        classic_report["profile_source"] = source

        # 2. Evaluate hybrid ML AI
        ai_report = evaluate_profiles(profiles, use_ai=True)
        ai_report["profile_source"] = source

        # 3. Test natural language concierge query
        sample_queries = [
            "Cozy romantic suite in Kigali with pool under $200",
            "Quiet workspace with fast Wi-Fi and breakfast in Nairobi",
        ]
        concierge_results = []
        for q in sample_queries:
            res = get_ai_concierge_recommendations(query=q, limit=2)
            concierge_results.append({
                "query": q,
                "engine_used": res["engine"],
                "extracted_hints": {
                    "city": res["hints"].get("city"),
                    "room_type": res["hints"].get("room_type"),
                    "max_price": str(res["hints"].get("max_price")) if res["hints"].get("max_price") else None,
                    "amenities": list(res["hints"].get("amenities", [])),
                    "vibes": res["hints"].get("vibes", []),
                },
                "summary": res["summary"],
                "top_recommendations": [
                    {
                        "room": item["room"].name,
                        "hotel": item["room"].hotel.name,
                        "score": item["score"],
                        "concierge_note": item.get("ai_concierge_note"),
                    }
                    for item in res["recommendations"][:2]
                ]
            })

        output = {
            "status": get_ai_engine_status(),
            "classic_baseline": classic_report,
            "hybrid_ai_engine": ai_report,
            "concierge_query_tests": concierge_results,
        }
        self.stdout.write(json.dumps(output, indent=2))
