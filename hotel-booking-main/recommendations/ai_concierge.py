"""
AI Travel Concierge & Natural Language Search for Staywise.

Interprets freeform natural language trip queries, extracts structured
travel constraints, scores rooms using Hybrid ML, and generates personalized
concierge recommendations and explanations.

Supports Google Gemini and OpenAI with a seamless, 100% offline local fallback.
"""

from decimal import Decimal
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request

from django.conf import settings
from hotels.models import Amenity, Hotel, Room
from .ai_engine import HybridRoomRecommender

logger = logging.getLogger(__name__)

# Heuristic patterns for extracting constraints from natural queries
BUDGET_PATTERN = re.compile(
    r"(?:under|below|less than|max|budget(?: of)?|upto|up to|\$)\s*(\$?\d+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)
GUEST_PATTERN = re.compile(
    r"(\d+)\s*(?:guest|guests|people|persons|adult|adults)|(?:family of\s*(\d+))",
    re.IGNORECASE,
)
ROOM_TYPE_KEYWORDS = {
    "suite": "suite",
    "deluxe": "deluxe",
    "standard": "standard",
    "family": "family",
    "penthouse": "suite",
    "villa": "suite",
}


def get_known_cities() -> List[str]:
    """Retrieve distinct hotel cities from the database or fall back to known seeds."""
    try:
        cities = list(Hotel.objects.values_list("city", flat=True).distinct())
        if cities:
            return [c for c in cities if c]
    except Exception:
        pass
    return ["Kigali", "Nairobi", "Zanzibar"]


def get_known_amenities() -> Dict[str, str]:
    """Map search terms to standard Amenity names."""
    try:
        db_amenities = {a.name.lower(): a.name for a in Amenity.objects.all()}
    except Exception:
        db_amenities = {}
    base_mapping = {
        "wifi": "Fast Wi-Fi",
        "wi-fi": "Fast Wi-Fi",
        "internet": "Fast Wi-Fi",
        "pool": "Pool",
        "swimming": "Pool",
        "swimming pool": "Pool",
        "spa": "Spa",
        "massage": "Spa",
        "wellness": "Spa",
        "breakfast": "Breakfast",
        "ocean view": "Ocean view",
        "beach": "Ocean view",
        "sea": "Ocean view",
        "workspace": "Workspace",
        "desk": "Workspace",
        "work": "Workspace",
    }
    base_mapping.update(db_amenities)
    return base_mapping


class AIConcierge:
    """
    AI Concierge providing natural language trip discovery,
    hybrid ML scoring, and personalized explanations.
    """

    def __init__(self):
        self.ml_recommender = HybridRoomRecommender()
        self.gemini_api_key = getattr(settings, "GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
        self.openai_api_key = getattr(settings, "OPENAI_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")

    def parse_query(self, query_text: str) -> Dict[str, Any]:
        """
        Extract structured travel constraints from freeform natural language.
        """
        if not query_text:
            return {}

        hints: Dict[str, Any] = {
            "city": None,
            "room_type": None,
            "max_price": None,
            "guests": None,
            "amenities": set(),
            "vibes": [],
        }

        query_lower = query_text.lower()

        # 1. Destination / City
        for city in get_known_cities():
            if city.lower() in query_lower:
                hints["city"] = city
                break

        # 2. Room Type
        for kw, r_type in ROOM_TYPE_KEYWORDS.items():
            if re.search(rf"\b{kw}\b", query_lower):
                hints["room_type"] = r_type
                break

        # 3. Budget
        budget_match = BUDGET_PATTERN.search(query_text)
        if budget_match:
            raw_val = budget_match.group(1).replace("$", "")
            try:
                hints["max_price"] = Decimal(raw_val)
            except Exception:
                pass

        # 4. Guests
        guest_match = GUEST_PATTERN.search(query_text)
        if guest_match:
            g_str = guest_match.group(1) or guest_match.group(2)
            try:
                hints["guests"] = int(g_str)
            except Exception:
                pass
        elif "couple" in query_lower or "romantic" in query_lower:
            hints["guests"] = 2
        elif "solo" in query_lower:
            hints["guests"] = 1

        # 5. Amenities
        amenity_map = get_known_amenities()
        for term, amenity_name in amenity_map.items():
            if term in query_lower:
                hints["amenities"].add(amenity_name.lower())

        # 6. Trip Vibe / Mood
        vibe_keywords = ["romantic", "luxury", "budget", "quiet", "peaceful", "scenic", "family", "work", "beach"]
        for vibe in vibe_keywords:
            if vibe in query_lower:
                hints["vibes"].append(vibe)

        return hints

    def call_gemini(self, query: str, candidate_rooms: List[Any], hints: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call Google Gemini API if key is available."""
        if not self.gemini_api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        
        rooms_summary = [
            {
                "id": r.pk,
                "name": r.name,
                "type": r.room_type,
                "price": str(r.price_per_night),
                "hotel": r.hotel.name,
                "city": r.hotel.city,
                "rating": str(r.hotel.rating),
                "amenities": [a.name for a in r.amenities.all()] + [a.name for a in r.hotel.amenities.all()],
            }
            for r in candidate_rooms[:6]
        ]

        system_instruction = (
            "You are Staywise AI, a sophisticated luxury hotel concierge. "
            "Analyze the traveler's request and the available hotel rooms. "
            "Provide a warm, personalized 2-sentence summary and 1-sentence concierge note for each room. "
            "Respond ONLY with a JSON object: {\"summary\": \"...\", \"room_notes\": {\"<id>\": \"note\"}}"
        )

        prompt_payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_instruction}\nUser request: \"{query}\"\nAvailable rooms: {json.dumps(rooms_summary)}"
                }]
            }],
            "generationConfig": {"temperature": 0.2, "response_mime_type": "application/json"}
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(prompt_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                result = json.loads(response.read().decode("utf-8"))
                text_content = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content)
        except Exception as exc:
            logger.warning("Gemini API call failed (%s); using offline fallback.", exc)
            return None

    def call_openai(self, query: str, candidate_rooms: List[Any], hints: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call OpenAI API if key is available."""
        if not self.openai_api_key:
            return None

        url = "https://api.openai.com/v1/chat/completions"
        rooms_summary = [
            {
                "id": r.pk,
                "name": r.name,
                "price": str(r.price_per_night),
                "hotel": r.hotel.name,
                "city": r.hotel.city,
                "rating": str(r.hotel.rating),
            }
            for r in candidate_rooms[:6]
        ]

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "You are Staywise AI concierge. Return JSON with 'summary' and 'room_notes' dict (room ID to note)."
                },
                {
                    "role": "user",
                    "content": f"Request: \"{query}\"\nRooms: {json.dumps(rooms_summary)}"
                }
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.openai_api_key}",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                result = json.loads(response.read().decode("utf-8"))
                text_content = result["choices"][0]["message"]["content"]
                return json.loads(text_content)
        except Exception as exc:
            logger.warning("OpenAI API call failed (%s); using offline fallback.", exc)
            return None

    def generate_offline_concierge_narrative(
        self,
        query: str,
        hints: Dict[str, Any],
        ranked_items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Intelligent Local NLP generator when offline or when no API key is provided.
        Synthesizes a realistic, personalized concierge summary and room notes.
        """
        count = len(ranked_items)
        city = hints.get("city")
        room_type = hints.get("room_type")
        max_price = hints.get("max_price")
        vibes = hints.get("vibes", [])

        # Build narrative summary
        summary_parts = []
        if query:
            summary_parts.append(f"We analyzed your search for \"{query}\".")
        else:
            summary_parts.append("We curated stays matching your profile and preferences.")

        criteria = []
        if city:
            criteria.append(f"in {city}")
        if room_type:
            criteria.append(f"{room_type} accommodations")
        if max_price:
            criteria.append(f"under ${float(max_price):.0f}/night")
        if vibes:
            criteria.append(f"with a {' and '.join(vibes)} atmosphere")

        if criteria:
            summary_parts.append(f"Prioritizing {', '.join(criteria)}, here are the {count} top-performing matches.")
        else:
            summary_parts.append(f"Found {count} standout stays ranked by semantic relevance, guest rating, and overall value.")

        summary = " ".join(summary_parts)

        # Build room-specific concierge notes
        room_notes = {}
        for item in ranked_items:
            room = item["room"]
            notes = []
            if float(room.hotel.rating) >= 4.7:
                notes.append(f"Exceptional {room.hotel.rating}★ hospitality in {room.hotel.city}")
            elif city and city.lower() in room.hotel.city.lower():
                notes.append(f"Centrally situated in your destination of {room.hotel.city}")

            amenity_names = [a.name for a in room.amenities.all()]
            if amenity_names:
                notes.append(f"features {', '.join(amenity_names[:2])}")

            if max_price and Decimal(str(room.price_per_night)) <= max_price:
                notes.append("stays comfortably within your requested budget")

            note_text = f"{room.name} at {room.hotel.name} " + (", ".join(notes) if notes else "offers exceptional comfort and value") + "."
            room_notes[str(room.pk)] = note_text

        return {
            "summary": summary,
            "room_notes": room_notes,
        }

    def recommend(
        self,
        query: Optional[str] = None,
        preference: Optional[Any] = None,
        check_in: Optional[Any] = None,
        check_out: Optional[Any] = None,
        guests: Optional[int] = None,
        limit: int = 12,
    ) -> Dict[str, Any]:
        """
        Run the complete AI concierge recommendation pipeline:
        1. Parse natural language query
        2. Query and filter candidate rooms (hard constraints: status, dates, capacity)
        3. Score & rank rooms with Hybrid ML recommender
        4. Generate AI concierge summary and room notes (LLM or intelligent local fallback)
        """
        hints = self.parse_query(query) if query else {}

        # Effective constraints (query hints override user preference)
        effective_guests = hints.get("guests") or guests or (getattr(preference, "guests", 2) if preference else 2)
        effective_check_in = check_in or (getattr(preference, "requested_check_in", None) if preference else None)
        effective_check_out = check_out or (getattr(preference, "requested_check_out", None) if preference else None)

        # Candidate rooms query
        rooms_qs = Room.objects.filter(
            status="available",
            capacity__gte=effective_guests
        ).select_related("hotel").prefetch_related("amenities", "hotel__amenities")

        # Destination filter from query hint if specified
        if hints.get("city"):
            rooms_qs = rooms_qs.filter(hotel__city__icontains=hints["city"])

        # Date availability check
        if effective_check_in and effective_check_out:
            rooms_qs = rooms_qs.exclude(
                bookings__status="confirmed",
                bookings__check_in__lt=effective_check_out,
                bookings__check_out__gt=effective_check_in,
            )

        candidate_rooms = list(rooms_qs.distinct())

        # If strict city filter returned no rooms, relax it to show closest semantic matches
        if not candidate_rooms and hints.get("city"):
            relaxed_qs = Room.objects.filter(
                status="available",
                capacity__gte=effective_guests
            ).select_related("hotel").prefetch_related("amenities", "hotel__amenities")
            if effective_check_in and effective_check_out:
                relaxed_qs = relaxed_qs.exclude(
                    bookings__status="confirmed",
                    bookings__check_in__lt=effective_check_out,
                    bookings__check_out__gt=effective_check_in,
                )
            candidate_rooms = list(relaxed_qs.distinct())

        # Run Hybrid ML ranking
        ranked_results = self.ml_recommender.rank_rooms(
            rooms=candidate_rooms,
            preference=preference,
            natural_query=query,
            extracted_hints=hints,
            limit=limit,
        )

        # Generate AI Concierge Summary (LLM or Local Fallback)
        engine_label = "Local Hybrid ML Recommender (Offline Smart Fallback)"
        ai_narrative = None

        if self.gemini_api_key:
            ai_narrative = self.call_gemini(query or "Recommend best stays", candidate_rooms, hints)
            if ai_narrative:
                engine_label = "Google Gemini AI"

        if not ai_narrative and self.openai_api_key:
            ai_narrative = self.call_openai(query or "Recommend best stays", candidate_rooms, hints)
            if ai_narrative:
                engine_label = "OpenAI GPT-4o-mini"

        if not ai_narrative:
            ai_narrative = self.generate_offline_concierge_narrative(query or "", hints, ranked_results)

        # Attach concierge notes to each ranked item
        notes_dict = ai_narrative.get("room_notes", {})
        for item in ranked_results:
            pk_str = str(item["room"].pk)
            if pk_str in notes_dict:
                item["ai_concierge_note"] = notes_dict[pk_str]
            else:
                item["ai_concierge_note"] = f"Top-rated stay in {item['room'].hotel.city} tailored to your itinerary."

        return {
            "query": query or "",
            "hints": hints,
            "engine": engine_label,
            "summary": ai_narrative.get("summary", ""),
            "recommendations": ranked_results,
            "total_matches": len(ranked_results),
        }

