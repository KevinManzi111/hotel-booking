from django.test import TestCase
from django.urls import reverse
from .models import Amenity, Hotel, Room

class HotelPagesTests(TestCase):
    def setUp(self):
        self.hotel = Hotel.objects.create(name="Test Lodge", city="Kigali", country="Rwanda", description="A calm stay", address="1 Test Road", rating="4.7", featured=True)
        self.room = Room.objects.create(hotel=self.hotel, name="Garden Suite", room_type="suite", description="Quiet and bright", price_per_night="120", capacity=2)
    def test_public_pages_render(self):
        for url in [reverse("hotels:home"), reverse("hotels:room_list"), reverse("hotels:room_detail", args=[self.room.pk])]:
            self.assertEqual(self.client.get(url).status_code, 200)
    def test_invalid_search_dates_show_error(self):
        response = self.client.get(reverse("hotels:room_list"), {"check_in":"2030-02-03", "check_out":"2030-02-02"})
        self.assertContains(response, "Check-out must be after check-in")
    def test_past_search_date_is_rejected(self):
        from datetime import timedelta
        from django.utils import timezone
        yesterday = timezone.localdate() - timedelta(days=1)
        response = self.client.get(reverse("hotels:room_list"), {"check_in":yesterday, "check_out":timezone.localdate()})
        self.assertContains(response, "Check-in cannot be in the past")
    def test_inactive_room_is_not_public(self):
        self.room.status = "maintenance"; self.room.save()
        self.assertEqual(self.client.get(reverse("hotels:room_detail", args=[self.room.pk])).status_code, 404)
    def test_price_guest_and_amenity_filters(self):
        wifi = Amenity.objects.create(name="Wi-Fi")
        self.room.amenities.add(wifi)
        other = Room.objects.create(hotel=self.hotel, name="Compact", room_type="standard", description="Small", price_per_night="60", capacity=1)
        response = self.client.get(reverse("hotels:room_list"), {"guests":2, "min_price":100, "max_price":150, "amenities":wifi.pk})
        self.assertContains(response, self.room.name)
        self.assertNotContains(response, other.name)
    def test_date_search_ignores_cancelled_and_excludes_confirmed(self):
        from bookings.models import Booking
        from django.contrib.auth.models import User
        from datetime import timedelta
        from django.utils import timezone
        user = User.objects.create_user("searcher")
        start = timezone.localdate() + timedelta(days=8); end = start + timedelta(days=2)
        Booking.objects.create(user=user, room=self.room, check_in=start, check_out=end, guests=1, status="cancelled")
        response = self.client.get(reverse("hotels:room_list"), {"check_in":start, "check_out":end})
        self.assertContains(response, self.room.name)
        Booking.objects.create(user=user, room=self.room, check_in=start, check_out=end, guests=1, status="confirmed")
        response = self.client.get(reverse("hotels:room_list"), {"check_in":start, "check_out":end})
        self.assertNotContains(response, self.room.name)
