from decimal import Decimal

from django.db import migrations


# Rooms that came from the imported Nairobi/Zanzibar demo inventory are
# re-homed onto the Rwandan hotels that use the traditional front-desk
# booking workflow this platform digitises.
ROOM_PLANS = {
    "NAI-STA-01": {
        "target_hotel": "TR5 Hotel & Suites",
        "identifier": "TR5-CAN-01",
        "name": "Ruyenzi Canopy King",
        "room_type": "deluxe",
        "bed_type": "king",
        "view_type": "garden",
        "price_per_night": Decimal("60.00"),
        "capacity": 2,
        "description": (
            "A refined king room with Rwandan woven accents and a calm garden "
            "outlook, a short drive from Kigali."
        ),
        "amenities": ["Breakfast", "Air conditioning", "Quiet room", "Garden view", "Fast Wi-Fi"],
    },
    "ZAN-DEL-01": {
        "target_hotel": "Kigali View Retreat",
        "identifier": "KGL-LKV-01",
        "name": "Kivu Skyline Deluxe",
        "room_type": "deluxe",
        "bed_type": "double",
        "view_type": "city",
        "price_per_night": Decimal("95.00"),
        "capacity": 2,
        "description": (
            "A spacious deluxe room on the Kiyovu ridge, drawing on Lake Kivu "
            "light with sweeping Kigali skyline views."
        ),
        "amenities": ["Breakfast", "Air conditioning", "City view", "Fast Wi-Fi", "Workspace"],
    },
}


def _unique_identifier(Room, desired, room_pk):
    """Return an identifier that is not already used by another room."""
    candidate = desired[:40]
    if not Room.objects.filter(identifier=candidate).exclude(pk=room_pk).exists():
        return candidate
    base = f"RW-{room_pk}-{desired}"[:32]
    candidate = base
    suffix = 1
    while Room.objects.filter(identifier=candidate).exclude(pk=room_pk).exists():
        candidate = f"{base[:36]}-{suffix}"
        suffix += 1
    return candidate


def rehome_foreign_rooms(apps, schema_editor):
    Hotel = apps.get_model("hotels", "Hotel")
    Room = apps.get_model("hotels", "Room")
    Amenity = apps.get_model("hotels", "Amenity")
    Booking = apps.get_model("bookings", "Booking")

    rwandan_hotels = list(
        Hotel.objects.filter(country__iexact="Rwanda").order_by("-featured", "-rating", "name")
    )
    if not rwandan_hotels:
        return
    by_name = {hotel.name: hotel for hotel in rwandan_hotels}

    foreign_rooms = list(
        Room.objects.select_related("hotel").exclude(hotel__country__iexact="Rwanda")
    )
    for room in foreign_rooms:
        plan = ROOM_PLANS.get(room.identifier)
        target = by_name.get(plan["target_hotel"]) if plan else None
        if target is None:
            target = next(
                (hotel for hotel in rwandan_hotels if hotel.city.lower() == room.hotel.city.lower()),
                rwandan_hotels[0],
            )

        # `seed_demo` may already have created the re-homed room. In that case
        # keep the canonical room, redirect any bookings, and drop the duplicate.
        existing = None
        if plan:
            existing = (
                Room.objects.filter(hotel=target, identifier=plan["identifier"])
                .exclude(pk=room.pk)
                .first()
            )
        if existing is not None:
            Booking.objects.filter(room=room).update(room=existing)
            room.delete()
            continue

        room.hotel = target
        if plan:
            room.identifier = _unique_identifier(Room, plan["identifier"], room.pk)
            for field in (
                "name",
                "room_type",
                "bed_type",
                "view_type",
                "price_per_night",
                "capacity",
                "description",
            ):
                setattr(room, field, plan[field])
        else:
            room.identifier = _unique_identifier(Room, f"RW-{room.identifier}", room.pk)
        room.save()

        if plan and plan.get("amenities"):
            room.amenities.set(Amenity.objects.filter(name__in=plan["amenities"]))

    # Remove the emptied non-Rwandan demo hotels so destination filters and
    # featured lists only surface Rwandan inventory.
    for hotel in Hotel.objects.exclude(country__iexact="Rwanda"):
        if not hotel.rooms.exists():
            hotel.amenities.clear()
            hotel.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("hotels", "0004_room_bed_type_room_has_ac_room_has_breakfast_and_more"),
        ("bookings", "0003_alter_booking_guests"),
    ]

    operations = [
        migrations.RunPython(rehome_foreign_rooms, migrations.RunPython.noop),
    ]
