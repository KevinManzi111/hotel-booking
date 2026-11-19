"""
Hybrid Machine Learning Recommendation Engine for EasyBooking.

Combines TF-IDF semantic vector representation and cosine similarity with
multi-criteria feature scoring (budget curve, amenity coverage, hotel ratings,
and capacity). Provides explainable feature attributions (XAI).
"""

from decimal import Decimal
import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

# Standard stop words for hospitality search domain
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "did", "do",
    "does", "doing", "don't", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
    "isn't", "it", "its", "itself", "just", "me", "more", "most", "my", "myself",
    "no", "nor", "not", "now", "of", "off", "on", "once", "only", "or", "other",
    "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so",
    "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too",
    "under", "until", "up", "very", "was", "wasn't", "we", "were", "weren't",
    "what", "when", "where", "which", "while", "who", "whom", "why", "with",
    "would", "you", "your", "yours", "yourself", "yourselves", "room", "hotel",
    "stay", "looking", "want", "need", "like", "place"
}

TOKEN_PATTERN = re.compile(r"\b[a-zA-Z0-9_\-]{2,}\b")


class TFIDFVectorizer:
    """
    Lightweight, high-performance TF-IDF vectorizer with n-grams (1-2)
    and cosine similarity. Works 100% offline with zero external dependencies.
    """

    def __init__(self, min_df: int = 1, use_bigrams: bool = True):
        self.min_df = min_df
        self.use_bigrams = use_bigrams
        self.vocabulary_: Dict[str, int] = {}
        self.idf_diag_: Dict[int, float] = {}
        self.doc_count_: int = 0

    def tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        raw_tokens = [t.lower() for t in TOKEN_PATTERN.findall(text)]
        tokens = [t for t in raw_tokens if t not in STOP_WORDS]
        if self.use_bigrams and len(tokens) >= 2:
            bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
            return tokens + bigrams
        return tokens

    def fit(self, documents: List[str]) -> "TFIDFVectorizer":
        self.doc_count_ = len(documents)
        df_counts: Dict[str, int] = {}
        for doc in documents:
            unique_terms = set(self.tokenize(doc))
            for term in unique_terms:
                df_counts[term] = df_counts.get(term, 0) + 1

        # Build vocabulary filtered by min_df
        filtered_terms = [t for t, count in df_counts.items() if count >= self.min_df]
        filtered_terms.sort()
        self.vocabulary_ = {term: idx for idx, term in enumerate(filtered_terms)}

        # Smoothed inverse document frequency: ln((1 + N) / (1 + df)) + 1
        self.idf_diag_ = {}
        for term, idx in self.vocabulary_.items():
            df = df_counts[term]
            self.idf_diag_[idx] = math.log((1.0 + self.doc_count_) / (1.0 + df)) + 1.0

        return self

    def transform(self, documents: List[str]) -> List[Dict[int, float]]:
        """Transform documents into sparse unit-length TF-IDF vectors."""
        vectors = []
        for doc in documents:
            tokens = self.tokenize(doc)
            term_freq: Dict[int, float] = {}
            for t in tokens:
                idx = self.vocabulary_.get(t)
                if idx is not None:
                    term_freq[idx] = term_freq.get(idx, 0.0) + 1.0

            if not term_freq:
                vectors.append({})
                continue

            # Sublinear TF scaling (1 + log(tf)) * idf
            weighted = {}
            for idx, count in term_freq.items():
                tf = 1.0 + math.log(count)
                weighted[idx] = tf * self.idf_diag_[idx]

            # L2 normalization to unit vector
            norm = math.sqrt(sum(v * v for v in weighted.values()))
            if norm > 0:
                vectors.append({idx: val / norm for idx, val in weighted.items()})
            else:
                vectors.append({})
        return vectors

    def compute_similarity(self, vec_a: Dict[int, float], vec_b: Dict[int, float]) -> float:
        """Cosine similarity between two unit vectors (dot product)."""
        if not vec_a or not vec_b:
            return 0.0
        # Iterate over the smaller vector
        if len(vec_a) > len(vec_b):
            vec_a, vec_b = vec_b, vec_a
        return sum(val * vec_b.get(idx, 0.0) for idx, val in vec_a.items())


class HybridRoomRecommender:
    """
    Hybrid Machine Learning Recommender for hotel rooms.
    Combines TF-IDF semantic embeddings with structured multi-criteria ranking.
    """

    DEFAULT_WEIGHTS = {
        "semantic": 0.35,
        "budget": 0.25,
        "amenity": 0.20,
        "rating": 0.10,
        "location": 0.10,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self._normalize_weights()
        self.vectorizer = TFIDFVectorizer(min_df=1, use_bigrams=True)
        self.is_fitted = False
        self._room_vectors: Dict[int, Dict[int, float]] = {}
        self._room_corpus: Dict[int, str] = {}

    def _normalize_weights(self):
        total = sum(max(0.0, float(v)) for v in self.weights.values())
        if total <= 0:
            self.weights = self.DEFAULT_WEIGHTS.copy()
            total = sum(self.weights.values())
        self.weights = {k: max(0.0, float(v)) / total for k, v in self.weights.items()}

    @staticmethod
    def extract_room_text(room) -> str:
        """Compile a rich descriptive document for a room and its parent hotel."""
        room_amenities = " ".join(a.name for a in room.amenities.all())
        hotel_amenities = " ".join(a.name for a in room.hotel.amenities.all())
        parts = [
            room.name,
            room.get_room_type_display() if hasattr(room, "get_room_type_display") else room.room_type,
            room.get_bed_type_display() if hasattr(room, "get_bed_type_display") else getattr(room, "bed_type", ""),
            room.get_view_type_display() if hasattr(room, "get_view_type_display") else getattr(room, "view_type", ""),
            "breakfast included" if getattr(room, "has_breakfast", False) else "",
            "air conditioning" if getattr(room, "has_ac", False) else "",
            "quiet room low noise" if getattr(room, "is_quiet", False) else "",
            room.description or "",
            room.hotel.name,
            room.hotel.city,
            room.hotel.country,
            room.hotel.description or "",
            room_amenities,
            hotel_amenities,
        ]
        return " ".join(p for p in parts if p)

    def fit_rooms(self, rooms: List[Any]) -> "HybridRoomRecommender":
        """Fit TF-IDF on the available room catalog."""
        self._room_corpus = {room.pk: self.extract_room_text(room) for room in rooms}
        docs = list(self._room_corpus.values())
        if docs:
            self.vectorizer.fit(docs)
            vectors = self.vectorizer.transform(docs)
            self._room_vectors = {room.pk: vec for room, vec in zip(rooms, vectors)}
        self.is_fitted = True
        return self

    def build_query_text(
        self,
        preference: Optional[Any] = None,
        natural_query: Optional[str] = None
    ) -> str:
        """Compose search text from user preferences and/or freeform prompt."""
        parts = []
        if natural_query:
            parts.append(natural_query)
        if preference:
            if getattr(preference, "preferred_city", None):
                parts.append(preference.preferred_city)
            if getattr(preference, "preferred_room_type", None):
                parts.append(preference.preferred_room_type)
            if getattr(preference, "preferred_bed_type", None):
                parts.append(preference.get_preferred_bed_type_display() if hasattr(preference, "get_preferred_bed_type_display") else preference.preferred_bed_type)
            if getattr(preference, "preferred_view", None):
                parts.append(preference.get_preferred_view_display() if hasattr(preference, "get_preferred_view_display") else preference.preferred_view)
            if getattr(preference, "requires_breakfast", False):
                parts.append("breakfast included")
            if getattr(preference, "requires_ac", False):
                parts.append("air conditioning")
            if getattr(preference, "requires_quiet", False):
                parts.append("quiet room")
            if hasattr(preference, "amenities"):
                if hasattr(preference.amenities, "all"):
                    parts.extend(a.name for a in preference.amenities.all() if hasattr(a, "name"))
                elif hasattr(preference.amenities, "values_list"):
                    parts.extend(str(x) for x in preference.amenities.values_list("name", flat=True))
        return " ".join(parts)

    def _score_budget(self, room_price: Any, max_price: Optional[Any]) -> float:
        """Soft budget curve: 1.0 within budget; linear decline to 0.0 at 150% budget."""
        if max_price in (None, "", 0):
            return 0.7  # Neutral score when unconstrained
        price = Decimal(str(room_price))
        budget = Decimal(str(max_price))
        if budget <= 0:
            return 0.0
        if price <= budget:
            return 1.0
        overshoot = float((price - budget) / (budget * Decimal("0.5")))
        return max(0.0, 1.0 - overshoot)

    def _score_amenities(self, room, preference, wanted_names: Optional[Set[str]] = None) -> Tuple[float, Set[str]]:
        """Calculate amenity intersection ratio."""
        if wanted_names is None:
            if preference and hasattr(preference, "amenities"):
                if hasattr(preference.amenities, "all"):
                    wanted_names = {a.name.lower() for a in preference.amenities.all() if hasattr(a, "name")}
                elif hasattr(preference.amenities, "values_list"):
                    wanted_names = {str(x).lower() for x in preference.amenities.values_list("name", flat=True)}
                else:
                    wanted_names = set()
            else:
                wanted_names = set()

        if not wanted_names:
            return 0.7, set()  # Neutral when no specific amenities requested

        room_amenities = {a.name.lower() for a in room.amenities.all()}
        hotel_amenities = {a.name.lower() for a in room.hotel.amenities.all()}
        offered = room_amenities | hotel_amenities
        matched = wanted_names & offered
        score = len(matched) / len(wanted_names)
        return score, matched

    def _score_rating(self, hotel_rating: Any) -> float:
        """Normalize hotel rating 0.0 - 5.0 to [0, 1]."""
        try:
            rating = float(hotel_rating)
            return min(max(rating / 5.0, 0.0), 1.0)
        except (ValueError, TypeError):
            return 0.5

    def _score_location(self, room, preferred_city: Optional[str]) -> float:
        """Location match score."""
        if not preferred_city:
            return 0.7  # Neutral
        loc = f"{room.hotel.city} {room.hotel.country}".casefold()
        return 1.0 if preferred_city.casefold() in loc else 0.0

    def score_room(
        self,
        room,
        preference: Optional[Any] = None,
        natural_query: Optional[str] = None,
        extracted_hints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Produce a full hybrid ML score and explainability attribution for a single room.
        """
        # 1. Semantic Similarity
        query_text = self.build_query_text(preference, natural_query)
        if query_text and self.is_fitted:
            query_vec = self.vectorizer.transform([query_text])[0]
            room_vec = self._room_vectors.get(room.pk)
            if room_vec is None:
                room_text = self.extract_room_text(room)
                room_vec = self.vectorizer.transform([room_text])[0]
            semantic_score = self.vectorizer.compute_similarity(query_vec, room_vec)
        else:
            semantic_score = 0.5

        # 2. Extract constraints from preference or hints
        hints = extracted_hints or {}
        max_price = hints.get("max_price") or (getattr(preference, "max_price", None) if preference else None)
        preferred_city = hints.get("city") or (getattr(preference, "preferred_city", None) if preference else None)
        wanted_amenities = hints.get("amenities")

        # 3. Component Scores
        budget_score = self._score_budget(room.price_per_night, max_price)
        amenity_score, matched_amenities = self._score_amenities(room, preference, wanted_amenities)
        rating_score = self._score_rating(room.hotel.rating)
        location_score = self._score_location(room, preferred_city)

        raw_scores = {
            "semantic": round(semantic_score, 4),
            "budget": round(budget_score, 4),
            "amenity": round(amenity_score, 4),
            "rating": round(rating_score, 4),
            "location": round(location_score, 4),
        }

        # 4. Weighted Aggregate
        contributions = {
            k: round(raw_scores[k] * self.weights[k] * 100, 1) for k in self.weights
        }
        total_score = min(100.0, max(0.0, round(sum(contributions.values()), 1)))

        # 5. Explainable AI (XAI) Reasons
        reasons = []
        if semantic_score > 0.35 and natural_query:
            reasons.append("Strong semantic alignment with your travel search")
        elif semantic_score > 0.25:
            reasons.append("Matches the ambiance and style of your preferences")

        if budget_score == 1.0 and max_price:
            reasons.append(f"Comfortably within your ${float(max_price):.0f} nightly budget")
        elif budget_score > 0.4 and max_price:
            reasons.append(f"Close to your ${float(max_price):.0f} target with premium features")

        if location_score == 1.0:
            reasons.append(f"Prime location in {room.hotel.city}")

        if matched_amenities:
            sample = list(matched_amenities)[:2]
            reasons.append(f"Offers requested features: {', '.join(t.title() for t in sample)}")

        if room.hotel.rating and float(room.hotel.rating) >= 4.5:
            reasons.append(f"Highly rated property ({room.hotel.rating}★)")

        if not reasons:
            reasons = ["Recommended stay based on catalog quality and price efficiency"]

        # Confidence categorization
        if total_score >= 80:
            confidence = "High"
        elif total_score >= 60:
            confidence = "Good"
        else:
            confidence = "Moderate"

        return {
            "room": room,
            "score": total_score,
            "confidence": confidence,
            "reasons": reasons[:4],
            "breakdown": {
                key: {
                    "raw": round(raw_scores[key] * 100),
                    "weight": round(self.weights[key] * 100),
                    "points": contributions[key],
                }
                for key in self.weights
            },
            "is_ai_recommended": True,
        }

    def rank_rooms(
        self,
        rooms: List[Any],
        preference: Optional[Any] = None,
        natural_query: Optional[str] = None,
        extracted_hints: Optional[Dict[str, Any]] = None,
        limit: int = 12,
    ) -> List[Dict[str, Any]]:
        """Fit and rank rooms, sorted by total hybrid score descending."""
        if not rooms:
            return []
        self.fit_rooms(rooms)
        scored = [
            self.score_room(r, preference, natural_query, extracted_hints)
            for r in rooms
        ]
        # Sort by score descending, then price ascending, then room pk
        scored.sort(
            key=lambda item: (
                -item["score"],
                Decimal(str(item["room"].price_per_night)),
                item["room"].pk,
            )
        )
        return scored[:limit]
