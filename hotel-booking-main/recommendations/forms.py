from django import forms
from bookings.forms import set_date_limits
from .models import UserPreference


class PreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = (
            "preferred_city",
            "preferred_room_type",
            "preferred_bed_type",
            "preferred_view",
            "requires_breakfast",
            "requires_ac",
            "requires_quiet",
            "max_price",
            "guests",
            "requested_check_in",
            "requested_check_out",
            "ai_travel_vibe",
            "amenities",
        )
        widgets = {
            "max_price": forms.NumberInput(attrs={"min": 1, "step": "0.01"}),
            "guests": forms.NumberInput(attrs={"min": 1}),
            "requested_check_in": forms.DateInput(attrs={"type": "date"}),
            "requested_check_out": forms.DateInput(attrs={"type": "date"}),
            "ai_travel_vibe": forms.TextInput(attrs={"placeholder": "e.g. Romantic getaway, quiet workspace, scenic hill view"}),
            "amenities": forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # No past dates in the stay-date calendars (recalculated on every request)
        set_date_limits(self, "requested_check_in", "requested_check_out")
