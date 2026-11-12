from datetime import timedelta
import json
from unittest.mock import MagicMock, patch
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from bookings.models import Booking
from hotels.models import Amenity, Hotel, Room
from .ai_concierge import AIConcierge
from .ai_engine import HybridRoomRecommender, TFIDFVectorizer
from .models import AIRecommendationQuery, UserPreference
from .services import (
    _budget_score,
    evaluate_profiles,
    get_ai_concierge_recommendations,
    get_ai_engine_status,
    get_weights,
    recommendations_for,
    score_room,
)


class RecommendationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("guest")
        self.wifi = Amenity.objects.create(name="Fast Wi-Fi")
        self.pool = Amenity.objects.create(name="Pool")
        self.hotel = Hotel.objects.create(name="Harbour", city="Kigali", country="Rwanda", description="Test luxury hotel", address="Road", rating="4.8")
        self.room = Room.objects.create(hotel=self.hotel, identifier="KGL-101", name="Suite", room_type="suite", description="Spacious suite with garden views", price_per_night="100", capacity=2)
        self.room.amenities.add(self.wifi)
        self.preference = UserPreference.objects.create(user=self.user, preferred_city="Kigali", preferred_room_type="suite", max_price="150", guests=2)
        self.preference.amenities.add(self.wifi)

    def test_perfect_match_scores_100_with_explanation_and_breakdown(self):
        result = score_room(self.room, self.preference)
        self.assertEqual(result["score"], 100)
        self.assertTrue(result["reasons"])
        self.assertEqual(set(result["breakdown"]), {"budget", "location", "room_type", "amenities", "capacity"})

    @override_settings(RECOMMENDATION_WEIGHTS={"budget": 3, "location": 2, "room_type": 2, "amenities": 2, "capacity": 1})
    def test_weights_are_configurable_and_normalized(self):
        weights = get_weights()
        self.assertAlmostEqual(sum(weights.values()), 1)
        self.assertEqual(weights["budget"], .3)

    def test_budget_scoring_is_consistent(self):
        self.assertEqual(_budget_score("100", "100"), 1)
        self.assertEqual(_budget_score("150", "100"), 0)
        self.assertEqual(_budget_score("125", "100"), .5)
        self.assertEqual(_budget_score("100", None), .5)

    def test_capacity_is_a_hard_constraint(self):
        self.preference.guests = 3
        self.preference.save()
        self.assertEqual(recommendations_for(self.preference), [])

    def test_requested_dates_exclude_confirmed_overlap(self):
        start = timezone.localdate() + timedelta(days=10)
        end = start + timedelta(days=2)
        self.preference.requested_check_in = start
        self.preference.requested_check_out = end
        self.preference.save()
        Booking.objects.create(user=self.user, room=self.room, check_in=start, check_out=end, guests=1)
        self.assertEqual(recommendations_for(self.preference), [])

    def test_cancelled_booking_does_not_remove_room(self):
        start = timezone.localdate() + timedelta(days=10)
        end = start + timedelta(days=2)
        self.preference.requested_check_in = start
        self.preference.requested_check_out = end
        self.preference.save()
        Booking.objects.create(user=self.user, room=self.room, check_in=start, check_out=end, guests=1, status="cancelled")
        self.assertEqual(recommendations_for(self.preference)[0]["room"], self.room)

    def test_missing_and_empty_preferences_are_handled(self):
        empty_user = User.objects.create_user("open")
        empty = UserPreference.objects.create(user=empty_user, guests=1)
        result = recommendations_for(empty)[0]
        self.assertGreaterEqual(result["score"], 0)
        self.assertIn("Ranked consistently", " ".join(result["reasons"]))

    def test_ties_are_deterministic_by_price_then_id(self):
        second = Room.objects.create(hotel=self.hotel, identifier="KGL-102", name="Second", room_type="suite", description="Test", price_per_night="90", capacity=2)
        second.amenities.add(self.wifi)
        ranked = recommendations_for(self.preference)
        self.assertEqual([item["room"] for item in ranked[:2]], [second, self.room])

    def test_evaluation_reports_coverage(self):
        report = evaluate_profiles([self.preference])
        self.assertEqual(report["profiles_evaluated"], 1)
        self.assertEqual(report["catalogue_coverage"], 1)

    def test_recommendation_pages_and_dashboard_require_user_context(self):
        self.client.force_login(self.user)
        for url in [reverse("recommendations:preferences"), reverse("recommendations:list"), reverse("accounts:dashboard")]:
            self.assertEqual(self.client.get(url).status_code, 200)

    # ==================== AI RECOMMENDATION ENGINE TESTS ====================

    def test_tfidf_vectorizer_computes_semantic_similarity(self):
        vectorizer = TFIDFVectorizer()
        corpus = [
            "Luxury romantic suite with ocean view and swimming pool in Zanzibar",
            "Modern business studio with fast wifi and executive workspace in Nairobi",
        ]
        vectorizer.fit(corpus)
        vectors = vectorizer.transform(corpus)
        query_vec = vectorizer.transform(["romantic pool in Zanzibar"])[0]

        sim_zanzibar = vectorizer.compute_similarity(query_vec, vectors[0])
        sim_nairobi = vectorizer.compute_similarity(query_vec, vectors[1])

        self.assertGreater(sim_zanzibar, sim_nairobi)
        self.assertGreater(sim_zanzibar, 0.4)

    def test_hybrid_ai_scoring_and_attribution(self):
        recommender = HybridRoomRecommender()
        recommender.fit_rooms([self.room])
        result = recommender.score_room(
            self.room,
            preference=self.preference,
            natural_query="luxury suite in Kigali with fast wifi",
        )
        self.assertGreaterEqual(result["score"], 50.0)
        self.assertIn("breakdown", result)
        self.assertIn("semantic", result["breakdown"])
        self.assertIn("budget", result["breakdown"])
        self.assertTrue(result["is_ai_recommended"])
        self.assertTrue(len(result["reasons"]) > 0)

    def test_ai_concierge_query_parser(self):
        concierge = AIConcierge()
        hints = concierge.parse_query("Looking for a romantic suite in Kigali with pool under $180 for 2 guests")
        self.assertEqual(hints["city"], "Kigali")
        self.assertEqual(hints["room_type"], "suite")
        self.assertEqual(hints["max_price"], 180)
        self.assertEqual(hints["guests"], 2)
        self.assertIn("pool", hints["amenities"])
        self.assertIn("romantic", hints["vibes"])

    def test_ai_concierge_offline_recommendations(self):
        concierge_res = get_ai_concierge_recommendations(
            query="romantic suite in Kigali with fast wifi",
            preference=self.preference,
        )
        self.assertIn("Offline", concierge_res["engine"])
        self.assertTrue(len(concierge_res["summary"]) > 0)
        self.assertEqual(len(concierge_res["recommendations"]), 1)
        top_match = concierge_res["recommendations"][0]
        self.assertEqual(top_match["room"], self.room)
        self.assertIn("ai_concierge_note", top_match)

    def test_ai_engine_status_service(self):
        status = get_ai_engine_status()
        self.assertIn("label", status)
        self.assertTrue(status["offline_ready"])

    def test_recommendations_list_view_with_ai_query(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("recommendations:list"), {"q": "romantic suite", "mode": "ai"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Concierge Travel Analysis")
        self.assertContains(response, "Suite")

        # Verify query was logged
        self.assertTrue(AIRecommendationQuery.objects.filter(user=self.user, query_text="romantic suite").exists())

    def test_ai_concierge_api_endpoint(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("recommendations:ai_concierge_api"), {"q": "suite in Kigali"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode("utf-8"))
        self.assertEqual(data["status"], "success")
        self.assertTrue(len(data["results"]) >= 1)
        self.assertEqual(data["results"][0]["name"], "Suite")

    def test_evaluate_ai_recommender_management_command(self):
        # Call command and ensure it executes without error
        call_command("evaluate_ai_recommender")
