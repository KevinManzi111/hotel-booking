from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import PreferenceForm
from .models import UserPreference
from .services import get_weights, recommendations_for

@login_required
def preferences(request):
    preference, _ = UserPreference.objects.get_or_create(user=request.user)
    form = PreferenceForm(request.POST or None, instance=preference)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Your travel preferences have been updated."); return redirect("recommendations:list")
    return render(request, "recommendations/preferences.html", {"form": form})

@login_required
def recommendation_list(request):
    preference, _ = UserPreference.objects.get_or_create(user=request.user)
    results = recommendations_for(preference)[:12]
    return render(request, "recommendations/list.html", {"recommendations": results, "weights": get_weights(), "preference": preference})
