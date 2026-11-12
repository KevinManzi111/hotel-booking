from django import forms
from .models import UserPreference


class PreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = (
            "preferred_city",
            "preferred_room_type",
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
            "ai_travel_vibe": forms.TextInput(attrs={"placeholder": "e.g. Romantic getaway, quiet workspace, scenic escape"}),
            "amenities": forms.CheckboxSelectMultiple(),
        }
