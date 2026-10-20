from django import forms
from django.utils import timezone
from .models import Amenity

class RoomSearchForm(forms.Form):
    city = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={"placeholder": "Where would you like to stay?"}))
    check_in = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    check_out = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    guests = forms.IntegerField(required=False, min_value=1, initial=2, widget=forms.NumberInput(attrs={"min": 1}))
    min_price = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={"min": 0, "step": "1", "placeholder": "Min"}))
    max_price = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={"min": 0, "step": "1", "placeholder": "Max"}))
    amenities = forms.ModelMultipleChoiceField(required=False, queryset=Amenity.objects.all(), widget=forms.CheckboxSelectMultiple)

    def clean(self):
        data = super().clean()
        start, end = data.get("check_in"), data.get("check_out")
        if bool(start) != bool(end):
            missing = "check_out" if start else "check_in"
            self.add_error(missing, "Both check-in and check-out dates are required for date search.")
        if start and end and end <= start:
            self.add_error("check_out", "Check-out must be after check-in.")
        if start and start < timezone.localdate():
            self.add_error("check_in", "Check-in cannot be in the past.")
        if data.get("min_price") is not None and data.get("max_price") is not None and data["max_price"] < data["min_price"]:
            self.add_error("max_price", "Maximum price must be at least the minimum price.")
        return data
