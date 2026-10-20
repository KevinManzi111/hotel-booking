from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from bookings.models import Booking
from hotels.models import Amenity, Hotel, Room
from .models import UserPreference
from .services import _budget_score, evaluate_profiles, get_weights, recommendations_for, score_room

class RecommendationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("guest")
        self.wifi = Amenity.objects.create(name="Wi-Fi")
        self.pool = Amenity.objects.create(name="Pool")
        self.hotel = Hotel.objects.create(name="Harbour", city="Kigali", country="Rwanda", description="Test", address="Road", rating="4.8")
        self.room = Room.objects.create(hotel=self.hotel, identifier="KGL-101", name="Suite", room_type="suite", description="Test", price_per_night="100", capacity=2)
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
        self.preference.guests = 3; self.preference.save()
        self.assertEqual(recommendations_for(self.preference), [])

    def test_requested_dates_exclude_confirmed_overlap(self):
        start = timezone.localdate() + timedelta(days=10); end = start + timedelta(days=2)
        self.preference.requested_check_in = start; self.preference.requested_check_out = end; self.preference.save()
        Booking.objects.create(user=self.user, room=self.room, check_in=start, check_out=end, guests=1)
        self.assertEqual(recommendations_for(self.preference), [])

    def test_cancelled_booking_does_not_remove_room(self):
        start = timezone.localdate() + timedelta(days=10); end = start + timedelta(days=2)
        self.preference.requested_check_in = start; self.preference.requested_check_out = end; self.preference.save()
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
