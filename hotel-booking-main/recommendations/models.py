from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from hotels.models import Amenity, Room

class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hotel_preferences")
    preferred_city = models.CharField(max_length=100, blank=True)
    preferred_room_type = models.CharField(max_length=20, choices=Room.ROOM_TYPES, blank=True)
    max_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0.01)])
    guests = models.PositiveSmallIntegerField(default=2, validators=[MinValueValidator(1)])
    requested_check_in = models.DateField(null=True, blank=True)
    requested_check_out = models.DateField(null=True, blank=True)
    amenities = models.ManyToManyField(Amenity, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    def clean(self):
        errors = {}
        if bool(self.requested_check_in) != bool(self.requested_check_out):
            errors["requested_check_out" if self.requested_check_in else "requested_check_in"] = "Enter both stay dates."
        if self.requested_check_in and self.requested_check_out and self.requested_check_out <= self.requested_check_in:
            errors["requested_check_out"] = "Check-out must be after check-in."
        if self.requested_check_in and self.requested_check_in < timezone.localdate():
            errors["requested_check_in"] = "Check-in cannot be in the past."
        if errors: raise ValidationError(errors)
    def __str__(self): return f"Preferences for {self.user}"
