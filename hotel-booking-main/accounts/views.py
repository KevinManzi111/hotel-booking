from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django import forms
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import time
from .forms import ProfileForm, SignUpForm
from .services import dashboard_metrics, default_period
from bookings.models import Booking

def signup(request):
    if request.user.is_authenticated:
        return redirect("hotels:home")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Welcome to Staywise. Your account is ready.")
        return redirect("recommendations:preferences")
    return render(request, "accounts/signup.html", {"form": form})

def username_availability(request):
    """Return only validation state; never expose matching account data."""
    if request.method != "POST":
        return JsonResponse({"valid": False, "message": "POST required."}, status=405)
    now = time.monotonic()
    attempts = [stamp for stamp in request.session.get("username_checks", []) if now - stamp < 60]
    if len(attempts) >= 30:
        return JsonResponse({"valid": False, "message": "Please wait before checking again."}, status=429)
    attempts.append(now)
    request.session["username_checks"] = attempts
    username = request.POST.get("username", "")
    try:
        normalized = SignUpForm.base_fields["username"].clean(username)
    except forms.ValidationError as exc:
        return JsonResponse({"valid": False, "available": False, "message": exc.messages[0]})
    if len(normalized) < 3:
        return JsonResponse({"valid": False, "available": False, "message": "Use at least 3 characters."})
    available = not get_user_model().objects.filter(username__iexact=normalized).exists()
    return JsonResponse({"valid": True, "available": available, "message": "Username is available." if available else "That username is already taken."})

@login_required
def dashboard(request):
    from recommendations.models import UserPreference
    from recommendations.services import recommendations_for
    preference, _ = UserPreference.objects.get_or_create(user=request.user)
    bookings = request.user.bookings.select_related("room__hotel")
    today = timezone.localdate()
    upcoming = bookings.exclude(status="cancelled").filter(check_out__gt=today)
    past = bookings.exclude(status="cancelled").filter(check_out__lte=today)
    cancelled = bookings.filter(status="cancelled")
    context = {"recommendations": recommendations_for(preference)[:3], "upcoming": upcoming, "past": past, "cancelled": cancelled, "preference": preference, "booking_metrics": {"total": bookings.count(), "upcoming": upcoming.count(), "completed": past.count(), "cancelled": cancelled.count()}}
    return render(request, "accounts/dashboard.html", context)

@login_required
def profile_edit(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save(); messages.success(request, "Your profile has been updated."); return redirect("accounts:dashboard")
    return render(request, "accounts/profile_edit.html", {"form": form})

@staff_member_required
def staff_dashboard(request):
    default_start, default_end = default_period()
    try: start = datetime.strptime(request.GET.get("start", ""), "%Y-%m-%d").date()
    except ValueError: start = default_start
    try: end = datetime.strptime(request.GET.get("end", ""), "%Y-%m-%d").date()
    except ValueError: end = default_end
    if end < start: start, end = default_start, default_end
    metrics = dashboard_metrics(start, end)
    bookings = Booking.objects.select_related("user", "room__hotel")
    query, status = request.GET.get("q", "").strip(), request.GET.get("status", "")
    if query: bookings = bookings.filter(Q(reference__icontains=query) | Q(user__username__icontains=query) | Q(user__email__icontains=query) | Q(room__name__icontains=query) | Q(room__identifier__icontains=query))
    if status in dict(Booking.STATUS): bookings = bookings.filter(status=status)
    page = Paginator(bookings, 12).get_page(request.GET.get("page"))
    params = request.GET.copy(); params.pop("page", None)
    return render(request, "accounts/staff_dashboard.html", {"metrics": metrics, "start": start, "end": end, "page_obj": page, "booking_statuses": Booking.STATUS, "selected_status": status, "query": query, "querystring": params.urlencode()})
