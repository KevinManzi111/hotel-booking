from datetime import timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from hotels.models import Hotel, Room
from .models import Booking

class BookingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("guest", password="safe-test-password")
        hotel = Hotel.objects.create(name="Test", city="Kigali", country="Rwanda", description="Test", address="Road", rating="4.5")
        self.room = Room.objects.create(hotel=hotel, name="Suite", room_type="suite", description="Test", price_per_night="100", capacity=2)
        self.start = timezone.localdate() + timedelta(days=5); self.end = self.start + timedelta(days=2)
    def test_total_is_calculated(self):
        booking = Booking.objects.create(user=self.user, room=self.room, check_in=self.start, check_out=self.end, guests=2)
        self.assertEqual(booking.total_price, 200)
    def test_overlap_is_rejected(self):
        Booking.objects.create(user=self.user, room=self.room, check_in=self.start, check_out=self.end, guests=1)
        with self.assertRaises(ValidationError): Booking.objects.create(user=self.user, room=self.room, check_in=self.start + timedelta(days=1), check_out=self.end + timedelta(days=1), guests=1)
    def test_adjacent_dates_are_allowed(self):
        Booking.objects.create(user=self.user, room=self.room, check_in=self.start, check_out=self.end, guests=1)
        adjacent = Booking.objects.create(user=self.user, room=self.room, check_in=self.end, check_out=self.end + timedelta(days=2), guests=1)
        self.assertEqual(adjacent.status, "confirmed")
    def test_cancelled_booking_does_not_block_dates(self):
        Booking.objects.create(user=self.user, room=self.room, check_in=self.start, check_out=self.end, guests=1, status="cancelled")
        replacement = Booking.objects.create(user=self.user, room=self.room, check_in=self.start, check_out=self.end, guests=1)
        self.assertEqual(replacement.status, "confirmed")
    def test_invalid_dates_and_capacity_are_rejected(self):
        with self.assertRaises(ValidationError): Booking.objects.create(user=self.user, room=self.room, check_in=self.end, check_out=self.start, guests=1)
        with self.assertRaises(ValidationError): Booking.objects.create(user=self.user, room=self.room, check_in=self.start, check_out=self.end, guests=3)
    def test_price_is_derived_not_accepted_from_client(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("bookings:create", args=[self.room.pk]), {"check_in":self.start, "check_out":self.end, "guests":1, "total_price":"0.01"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Booking.objects.get().total_price, 200)
        self.assertTrue(Booking.objects.get().reference.startswith("STY-"))
    def test_booked_price_is_preserved_when_rate_later_changes(self):
        booking = Booking.objects.create(user=self.user, room=self.room, check_in=self.start, check_out=self.end, guests=1)
        self.room.price_per_night = 999; self.room.save()
        booking.status = "cancelled"; booking.save(update_fields=["status", "updated_at"])
        booking.refresh_from_db(); self.assertEqual(booking.total_price, 200)
    def test_zero_guests_are_rejected_by_model(self):
        with self.assertRaises(ValidationError): Booking.objects.create(user=self.user, room=self.room, check_in=self.start, check_out=self.end, guests=0)
    def test_booking_pages_require_login(self):
        response = self.client.get(reverse("bookings:create", args=[self.room.pk]))
        self.assertEqual(response.status_code, 302)
    def test_authenticated_booking_pages_render(self):
        self.client.force_login(self.user)
        booking = Booking.objects.create(user=self.user, room=self.room, check_in=self.start, check_out=self.end, guests=1)
        for url in [reverse("bookings:list"), reverse("bookings:create", args=[self.room.pk]), reverse("bookings:detail", args=[booking.pk])]:
            self.assertEqual(self.client.get(url).status_code, 200)
    def test_user_cannot_see_another_booking(self):
        other = User.objects.create_user("other", password="safe-test-password")
        booking = Booking.objects.create(user=other, room=self.room, check_in=self.start, check_out=self.end, guests=1)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("bookings:detail", args=[booking.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("bookings:cancel", args=[booking.pk])).status_code, 404)
    def test_cancellation_rules_and_post_only(self):
        booking = Booking.objects.create(user=self.user, room=self.room, check_in=timezone.localdate(), check_out=timezone.localdate() + timedelta(days=1), guests=1)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("bookings:cancel", args=[booking.pk])).status_code, 405)
        self.client.post(reverse("bookings:cancel", args=[booking.pk]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, "confirmed")
    def test_cancellation_requires_csrf(self):
        booking = Booking.objects.create(user=self.user, room=self.room, check_in=self.start, check_out=self.end, guests=1)
        client = Client(enforce_csrf_checks=True); client.force_login(self.user)
        self.assertEqual(client.post(reverse("bookings:cancel", args=[booking.pk])).status_code, 403)
