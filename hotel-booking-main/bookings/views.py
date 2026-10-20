from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from hotels.models import Room
from .forms import BookingForm
from .models import Booking

@login_required
def create_booking(request, room_id):
    room = get_object_or_404(Room.objects.select_related("hotel"), pk=room_id, status="available")
    initial = {key: request.GET.get(key) for key in ("check_in", "check_out", "guests") if request.GET.get(key)}
    form = BookingForm(request.POST or None, room=room, initial=initial)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            locked_room = Room.objects.select_for_update().get(pk=room.pk)
            booking = form.save(commit=False); booking.user = request.user; booking.room = locked_room
            try: booking.save()
            except ValidationError as exc:
                if hasattr(exc, "error_dict"):
                    for field, errors in exc.error_dict.items():
                        target = field if field in form.fields else None
                        for error in errors: form.add_error(target, error)
                else: form.add_error(None, exc)
            else:
                messages.success(request, "Your stay is booked. We look forward to welcoming you.")
                return redirect("bookings:detail", pk=booking.pk)
    return render(request, "bookings/booking_form.html", {"form": form, "room": room})

@login_required
def booking_list(request):
    return render(request, "bookings/booking_list.html", {"bookings": request.user.bookings.select_related("room__hotel")})

@login_required
def booking_detail(request, pk):
    return render(request, "bookings/booking_detail.html", {"booking": get_object_or_404(Booking.objects.select_related("room__hotel"), pk=pk, user=request.user)})

@require_POST
@login_required
def cancel_booking(request, pk):
    with transaction.atomic():
        booking = get_object_or_404(Booking.objects.select_for_update(), pk=pk, user=request.user)
        if booking.status == "cancelled": messages.info(request, "This booking was already cancelled.")
        elif not booking.can_cancel: messages.error(request, "This booking can no longer be cancelled online.")
        else:
            booking.status = "cancelled"; booking.save(update_fields=["status", "updated_at"]); messages.success(request, "Your booking has been cancelled.")
    return redirect("bookings:detail", pk=pk)
