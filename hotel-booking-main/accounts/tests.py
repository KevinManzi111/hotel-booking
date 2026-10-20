from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase
from django.test import RequestFactory
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from bookings.models import Booking
from hotels.models import Hotel, Room
from .services import dashboard_metrics

class AccountPagesTests(TestCase):
    def test_auth_pages_render(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)
        self.assertEqual(self.client.get(reverse("accounts:signup")).status_code, 200)

    def test_signup_creates_and_authenticates_user(self):
        response = self.client.post(reverse("accounts:signup"), {"first_name":"Amina", "last_name":"Test", "email":"amina@example.com", "username":"amina", "password1":"Correct-Horse-2026!", "password2":"Correct-Horse-2026!"})
        self.assertRedirects(response, reverse("recommendations:preferences"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_duplicate_email_registration_is_rejected(self):
        User.objects.create_user("existing", email="amina@example.com")
        response = self.client.post(reverse("accounts:signup"), {"first_name":"Amina", "last_name":"Test", "email":"AMINA@example.com", "username":"amina", "password1":"Correct-Horse-2026!", "password2":"Correct-Horse-2026!"})
        self.assertContains(response, "already exists")

    def test_username_availability_is_minimal_post_only_and_validated(self):
        url = reverse("accounts:username_availability")
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertFalse(self.client.post(url, {"username": "x"}).json()["valid"])
        available = self.client.post(url, {"username": "fresh-name"}).json()
        self.assertTrue(available["valid"]); self.assertTrue(available["available"])
        User.objects.create_user("fresh-name")
        taken = self.client.post(url, {"username": "FRESH-NAME"}).json()
        self.assertFalse(taken["available"])
        self.assertNotIn("email", taken)

    def test_login_and_post_logout(self):
        User.objects.create_user("member", password="safe-test-password")
        self.assertTrue(self.client.login(username="member", password="safe-test-password"))
        self.assertRedirects(self.client.post(reverse("logout")), reverse("hotels:home"))

    def test_all_django_message_levels_render_as_accessible_toasts(self):
        request = RequestFactory().get("/")
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)
        messages.success(request, "Success message")
        messages.error(request, "Error message")
        messages.warning(request, "Warning message")
        messages.info(request, "Information message")
        html = render_to_string("includes/messages.html", {"messages": request._messages}, request=request)
        self.assertEqual(html.count("data-toast data-level="), 4)
        self.assertIn('class="site-toast toast-success"', html)
        self.assertIn('class="site-toast toast-error"', html)
        self.assertIn('class="site-toast toast-warning"', html)
        self.assertIn('class="site-toast toast-info"', html)
        self.assertEqual(html.count('data-toast-dismiss'), 4)
        self.assertIn('role="alert"', html)
        self.assertIn('role="status"', html)

    def test_field_validation_remains_inline_not_a_toast(self):
        response = self.client.post(reverse("accounts:signup"), {"username": "x"})
        self.assertContains(response, "invalid-feedback")
        self.assertNotContains(response, "data-toast")

class DashboardTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user("customer", email="customer@example.com", password="test-pass")
        self.staff = User.objects.create_user("staff", password="test-pass", is_staff=True)
        hotel = Hotel.objects.create(name="Metrics Hotel", city="Kigali", country="Rwanda", description="Test", address="Road", rating="4.5")
        self.room = Room.objects.create(hotel=hotel, identifier="MET-1", name="Metrics Room", room_type="standard", description="Test", price_per_night="100", capacity=2)
        self.start = timezone.localdate() + timedelta(days=2); self.end = self.start + timedelta(days=7)

    def test_customer_dashboard_requires_login_and_uses_ownership(self):
        self.assertEqual(self.client.get(reverse("accounts:dashboard")).status_code, 302)
        Booking.objects.create(user=self.customer, room=self.room, check_in=self.start, check_out=self.start + timedelta(days=2), guests=1)
        self.client.force_login(self.customer)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertContains(response, "STY-")

    def test_profile_edit_only_changes_current_user(self):
        self.client.force_login(self.customer)
        response = self.client.post(reverse("accounts:profile_edit"), {"first_name":"New", "last_name":"Name", "email":"new@example.com"})
        self.assertRedirects(response, reverse("accounts:dashboard"))
        self.customer.refresh_from_db(); self.assertEqual(self.customer.email, "new@example.com")

    def test_staff_dashboard_permissions(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(reverse("accounts:staff_dashboard")).status_code, 302)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("accounts:staff_dashboard")).status_code, 200)

    def test_metrics_calculate_availability_status_and_revenue(self):
        booking = Booking.objects.create(user=self.customer, room=self.room, check_in=self.start, check_out=self.start + timedelta(days=2), guests=1)
        metrics = dashboard_metrics(self.start, self.end)
        self.assertEqual(metrics["total_rooms"], 1); self.assertEqual(metrics["available_rooms"], 0)
        self.assertEqual(metrics["status_counts"]["confirmed"], 1); self.assertEqual(metrics["revenue"], 200)

    def test_empty_metrics_and_booking_filters(self):
        metrics = dashboard_metrics(self.start, self.end)
        self.assertEqual(metrics["bookings_total"], 0); self.assertEqual(metrics["revenue"], 0)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("accounts:staff_dashboard"), {"q":"missing", "status":"cancelled", "start":self.start, "end":self.end})
        self.assertContains(response, "No bookings match these filters")

    def test_staff_booking_search_and_status_filter(self):
        booking = Booking.objects.create(user=self.customer, room=self.room, check_in=self.start, check_out=self.start + timedelta(days=1), guests=1)
        self.client.force_login(self.staff)
        response = self.client.get(reverse("accounts:staff_dashboard"), {"q":booking.reference, "status":"confirmed", "start":self.start, "end":self.end})
        self.assertContains(response, booking.reference)
