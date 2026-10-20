from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, render
from .forms import RoomSearchForm
from .models import Hotel, Room

def home(request):
    available_rooms = Room.objects.filter(status="available").select_related("hotel").prefetch_related("amenities")
    hotels = Hotel.objects.filter(featured=True, rooms__status="available").distinct().prefetch_related(Prefetch("rooms", queryset=available_rooms, to_attr="available_rooms"))[:3]
    return render(request, "hotels/home.html", {"featured_hotels": hotels, "search_form": RoomSearchForm()})

def room_list(request):
    form = RoomSearchForm(request.GET or None)
    rooms = Room.objects.filter(status="available").select_related("hotel").prefetch_related("amenities")
    if form.is_valid():
        city, guests = form.cleaned_data.get("city"), form.cleaned_data.get("guests")
        if city: rooms = rooms.filter(Q(hotel__city__icontains=city) | Q(hotel__country__icontains=city))
        if guests: rooms = rooms.filter(capacity__gte=guests)
        if form.cleaned_data.get("min_price") is not None: rooms = rooms.filter(price_per_night__gte=form.cleaned_data["min_price"])
        if form.cleaned_data.get("max_price") is not None: rooms = rooms.filter(price_per_night__lte=form.cleaned_data["max_price"])
        if form.cleaned_data.get("amenities"): rooms = rooms.filter(amenities__in=form.cleaned_data["amenities"]).distinct()
        start, end = form.cleaned_data.get("check_in"), form.cleaned_data.get("check_out")
        if start and end:
            unavailable = rooms.filter(bookings__status="confirmed", bookings__check_in__lt=end, bookings__check_out__gt=start).values_list("pk", flat=True)
            rooms = rooms.exclude(pk__in=unavailable)
    page = Paginator(rooms, 6).get_page(request.GET.get("page"))
    query = request.GET.copy(); query.pop("page", None)
    return render(request, "hotels/room_list.html", {"page_obj": page, "search_form": form, "querystring": query.urlencode()})

def room_detail(request, pk):
    room = get_object_or_404(Room.objects.select_related("hotel").prefetch_related("amenities", "hotel__amenities"), pk=pk, status="available")
    match = None
    if request.user.is_authenticated:
        from recommendations.models import UserPreference
        from recommendations.services import recommendation_for_room
        preference, _ = UserPreference.objects.get_or_create(user=request.user)
        match = recommendation_for_room(room, preference)
    return render(request, "hotels/room_detail.html", {"room": room, "recommendation_match": match})
