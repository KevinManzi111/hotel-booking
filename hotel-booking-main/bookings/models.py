from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
import uuid

def generate_booking_reference():
    return "STY-" + uuid.uuid4().hex[:10].upper()
from hotels.models import Room

class Booking(models.Model):
    STATUS = [("pending", "Pending"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled"), ("completed", "Completed")]
    reference = models.CharField(max_length=16, unique=True, editable=False, db_index=True, default=generate_booking_reference)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="bookings")
    check_in = models.DateField()
    check_out = models.DateField()
    guests = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)
    status = models.CharField(max_length=12, choices=STATUS, default="confirmed")
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def nights(self): return max((self.check_out - self.check_in).days, 0)
    @property
    def can_cancel(self): return self.status in {"pending", "confirmed"} and self.check_in > timezone.localdate()

    def clean(self):
        errors = {}
        if self.check_in and self.check_out and self.check_out <= self.check_in: errors["check_out"] = "Check-out must be after check-in."
        if self.check_in and self.check_in < timezone.localdate(): errors["check_in"] = "Check-in cannot be in the past."
        if self.room_id and self.guests > self.room.capacity: errors["guests"] = f"This room accommodates up to {self.room.capacity} guests."
        if self.room_id and self.check_in and self.check_out and self.status == "confirmed":
            overlap = Booking.objects.filter(room=self.room, status="confirmed", check_in__lt=self.check_out, check_out__gt=self.check_in).exclude(pk=self.pk).exists()
            if overlap: errors["check_in"] = "This room is no longer available for those dates."
        if errors: raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        reprice = self._state.adding
        if not reprice:
            original = Booking.objects.filter(pk=self.pk).values("room_id", "check_in", "check_out").first()
            reprice = not original or original["room_id"] != self.room_id or original["check_in"] != self.check_in or original["check_out"] != self.check_out
        if reprice:
            self.total_price = Decimal(self.nights) * Decimal(self.room.price_per_night)
        super().save(*args, **kwargs)
    def __str__(self): return f"{self.user} · {self.room} · {self.check_in}"
    class Meta: ordering = ["-created_at"]; indexes = [models.Index(fields=["room", "check_in", "check_out", "status"])]
