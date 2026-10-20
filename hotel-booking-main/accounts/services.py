from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.utils import timezone
from bookings.models import Booking
from hotels.models import Room

def default_period():
    today = timezone.localdate()
    return today, today + timedelta(days=30)

def dashboard_metrics(start, end):
    """Metrics for stays with check-in in inclusive [start, end]."""
    period_bookings = Booking.objects.filter(check_in__range=(start, end))
    blocking = Booking.objects.filter(status="confirmed", check_in__lt=end + timedelta(days=1), check_out__gt=start).values_list("room_id", flat=True)
    active_rooms = Room.objects.filter(status="available")
    statuses = {row["status"]: row["count"] for row in period_bookings.values("status").annotate(count=Count("id"))}
    revenue = period_bookings.filter(status__in=["confirmed", "completed"]).aggregate(total=Sum("total_price"))["total"] or Decimal("0")
    trends = period_bookings.values("check_in").annotate(bookings=Count("id"), revenue=Sum("total_price", filter=Q(status__in=["confirmed", "completed"]))).order_by("check_in")
    trend_map = {row["check_in"]: row for row in trends}
    labels, booking_values, revenue_values = [], [], []
    day = start
    while day <= end:
        row = trend_map.get(day, {})
        labels.append(day.isoformat()); booking_values.append(row.get("bookings", 0)); revenue_values.append(float(row.get("revenue") or 0)); day += timedelta(days=1)
    return {
        "total_rooms": Room.objects.count(), "active_rooms": active_rooms.count(),
        "available_rooms": active_rooms.exclude(pk__in=blocking).count(),
        "bookings_total": period_bookings.count(), "status_counts": {key: statuses.get(key, 0) for key, _ in Booking.STATUS},
        "cancellations": statuses.get("cancelled", 0), "revenue": revenue,
        "trend": {"labels": labels, "bookings": booking_values, "revenue": revenue_values},
        "customers": get_user_model().objects.filter(is_staff=False).count(),
    }
