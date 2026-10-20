from django import forms
from django.utils import timezone
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ("check_in", "check_out", "guests", "special_requests")
        widgets = {"check_in": forms.DateInput(attrs={"type": "date", "min": timezone.localdate().isoformat()}), "check_out": forms.DateInput(attrs={"type": "date"}), "special_requests": forms.Textarea(attrs={"rows": 3, "placeholder": "Accessibility needs, arrival time, or anything else we should know"})}

    def __init__(self, *args, room=None, **kwargs):
        super().__init__(*args, **kwargs); self.room = room

    def clean(self):
        data = super().clean(); start, end = data.get("check_in"), data.get("check_out")
        if start and end and end <= start: self.add_error("check_out", "Check-out must be after check-in.")
        if start and start < timezone.localdate(): self.add_error("check_in", "Check-in cannot be in the past.")
        if self.room and data.get("guests") and data["guests"] > self.room.capacity: self.add_error("guests", f"Maximum {self.room.capacity} guests.")
        return data
