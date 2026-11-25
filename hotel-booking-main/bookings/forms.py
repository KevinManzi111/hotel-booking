from datetime import timedelta
from django import forms
from django.utils import timezone
from .models import Booking


def set_date_limits(form, check_in_field, check_out_field):
    """Stop the browser date pickers offering past dates.

    check-in may be today at the earliest; check-out tomorrow at the earliest.
    This only guides the guest - clean() below still rejects past dates on the server.
    """
    today = timezone.localdate()                      # today in Africa/Kigali (settings.TIME_ZONE)
    form.fields[check_in_field].widget.attrs["min"] = today.isoformat()
    form.fields[check_out_field].widget.attrs["min"] = (today + timedelta(days=1)).isoformat()

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ("check_in", "check_out", "guests", "special_requests")
        widgets = {"check_in": forms.DateInput(attrs={"type": "date"}), "check_out": forms.DateInput(attrs={"type": "date"}), "special_requests": forms.Textarea(attrs={"rows": 3, "placeholder": "Accessibility needs, arrival time, or anything else we should know"})}

    def __init__(self, *args, room=None, **kwargs):
        super().__init__(*args, **kwargs); self.room = room
        # Set the calendar limits here (on every request), not in Meta.widgets:
        # values in Meta are calculated once when the server starts, so after
        # midnight the picker would still offer "yesterday".
        set_date_limits(self, "check_in", "check_out")

    def clean(self):
        data = super().clean(); start, end = data.get("check_in"), data.get("check_out")
        if start and end and end <= start: self.add_error("check_out", "Check-out must be after check-in.")
        if start and start < timezone.localdate(): self.add_error("check_in", "Check-in cannot be in the past.")
        if self.room and data.get("guests") and data["guests"] > self.room.capacity: self.add_error("guests", f"Maximum {self.room.capacity} guests.")
        return data
