from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from bookings.models import Booking
from hotels.models import Amenity, Hotel, Room
from recommendations.models import UserPreference


class Command(BaseCommand):
    help = "Seed the Rwandan hotels (TR5 in Ruyenzi and Kigali partners), rooms, amenities, and 10 test users"

    def handle(self, *args, **options):
        User = get_user_model()

        # 1. Amenities
        amenities = {}
        amenity_specs = [
            ("Breakfast", "bi-cup-hot"),
            ("Air conditioning", "bi-snow"),
            ("Quiet room", "bi-volume-mute"),
            ("Hill view", "bi-image"),
            ("Garden view", "bi-flower1"),
            ("City view", "bi-building"),
            ("Fast Wi-Fi", "bi-wifi"),
            ("Workspace", "bi-laptop"),
            ("Pool", "bi-water"),
            ("Spa", "bi-flower1"),
        ]
        for name, icon in amenity_specs:
            amenities[name], _ = Amenity.objects.get_or_create(name=name, defaults={"icon": icon})

        # 2. Hotels
        # Primary: TR5 Hotel in Ruyenzi, Rwanda
        tr5, _ = Hotel.objects.get_or_create(
            name="TR5 Hotel & Suites",
            defaults={
                "city": "Ruyenzi",
                "country": "Rwanda",
                "description": "TR5 Hotel in Ruyenzi is a modern, welcoming hotel offering peaceful stays, scenic hill views, and personalized hospitality just 15 minutes from Kigali.",
                "address": "Ruyenzi Center, Kamonyi (Kigali - Muhanga Road), Southern Province, Rwanda",
                "rating": Decimal("4.8"),
                "featured": True,
                "image_url": "/static/images/hero-hotel.png",
            }
        )

        # Kigali Partner Hotels (SME accommodation in Kigali)
        kigali_view, _ = Hotel.objects.get_or_create(
            name="Kigali View Retreat",
            defaults={
                "city": "Kigali",
                "country": "Rwanda",
                "description": "A boutique hotel situated on the Kiyovu ridge with sweeping skyline views and tranquil gardens.",
                "address": "KN 29 Street, Kiyovu, Kigali, Rwanda",
                "rating": Decimal("4.9"),
                "featured": True,
                "image_url": "/static/images/hero-hotel.png",
            }
        )

        inziza, _ = Hotel.objects.get_or_create(
            name="Inziza Boutique Hotel",
            defaults={
                "city": "Kigali",
                "country": "Rwanda",
                "description": "Contemporary Rwandan comfort in the heart of Kimihurura, close to dining and cultural spaces.",
                "address": "KG 674 Street, Kimihurura, Kigali, Rwanda",
                "rating": Decimal("4.7"),
                "featured": True,
                "image_url": "/static/images/hero-hotel.png",
            }
        )

        verdant, _ = Hotel.objects.get_or_create(
            name="The Verdant House",
            defaults={
                "city": "Kigali",
                "country": "Rwanda",
                "description": "A serene urban retreat where considered design meets warm Rwandan hospitality.",
                "address": "14 Palm Avenue, Kigali, Rwanda",
                "rating": Decimal("4.9"),
                "featured": True,
                "image_url": "/static/images/hero-hotel.png",
            }
        )

        # 3. Rooms
        room_records = [
            # TR5 Hotel Rooms (Ruyenzi)
            (tr5, "Deluxe Hill View Double", "TR5-DLX-01", "deluxe", "double", "hill", True, True, True, "45.00", 2, "A light-filled room overlooking the rolling hills of Kamonyi.", ["Breakfast", "Air conditioning", "Quiet room", "Hill view", "Fast Wi-Fi"]),
            (tr5, "Standard Single Room", "TR5-STD-01", "standard", "single", "garden", True, True, True, "30.00", 1, "A serene single room designed for solo travelers and business visits.", ["Breakfast", "Air conditioning", "Quiet room", "Garden view", "Fast Wi-Fi"]),
            (tr5, "Executive Hill Suite", "TR5-STE-01", "suite", "king", "hill", True, True, True, "70.00", 2, "Spacious master suite with private lounge and panoramic hill outlook.", ["Breakfast", "Air conditioning", "Quiet room", "Hill view", "Workspace", "Fast Wi-Fi"]),
            (tr5, "Comfort Twin Room", "TR5-TWN-01", "standard", "twin", "garden", True, True, True, "40.00", 2, "Twin beds with garden view, perfect for colleagues and travel partners.", ["Breakfast", "Air conditioning", "Quiet room", "Garden view", "Fast Wi-Fi"]),
            (tr5, "Family Valley Room", "TR5-FAM-01", "family", "queen", "courtyard", True, True, True, "65.00", 4, "Spacious family accommodation comfortably hosting up to four guests.", ["Breakfast", "Air conditioning", "Quiet room", "Fast Wi-Fi"]),
            # Kigali View Retreat
            (kigali_view, "Superior City King", "KGL-KNG-01", "deluxe", "king", "city", True, True, True, "85.00", 2, "Executive room with king bed and private balcony overlooking Kigali skyline.", ["Breakfast", "Air conditioning", "Quiet room", "Fast Wi-Fi", "Workspace"]),
            (kigali_view, "Classic Double Kigali", "KGL-DBL-01", "standard", "double", "garden", True, True, False, "55.00", 2, "A welcoming room near central Kigali with courtyard garden outlook.", ["Breakfast", "Air conditioning", "Fast Wi-Fi"]),
            # Inziza Boutique Hotel
            (inziza, "Garden Terrace Suite", "INZ-STE-01", "suite", "queen", "garden", True, True, True, "90.00", 2, "Artisan-furnished suite with private patio terrace and serene greenery.", ["Breakfast", "Air conditioning", "Quiet room", "Garden view", "Fast Wi-Fi"]),
            (inziza, "Cozy Studio Double", "INZ-STD-01", "standard", "double", "courtyard", True, True, True, "50.00", 2, "Comfortable urban double room in Kimihurura.", ["Breakfast", "Air conditioning", "Quiet room", "Fast Wi-Fi"]),
            # The Verdant House
            (verdant, "Garden Suite", "KIG-SUI-01", "suite", "double", "garden", True, True, True, "185.00", 2, "A light-filled suite with a private lounge and garden outlook.", ["Breakfast", "Air conditioning", "Quiet room", "Garden view", "Fast Wi-Fi"]),
            # Re-homed from the former Nairobi and Zanzibar demo inventory so every
            # stay belongs to a Rwandan property using traditional front-desk booking.
            (tr5, "Ruyenzi Canopy King", "TR5-CAN-01", "deluxe", "king", "garden", True, True, True, "60.00", 2, "A refined king room with Rwandan woven accents and a calm garden outlook, a short drive from Kigali.", ["Breakfast", "Air conditioning", "Quiet room", "Garden view", "Fast Wi-Fi"]),
            (kigali_view, "Kivu Skyline Deluxe", "KGL-LKV-01", "deluxe", "double", "city", True, True, True, "95.00", 2, "A spacious deluxe room on the Kiyovu ridge, drawing on Lake Kivu light with sweeping Kigali skyline views.", ["Breakfast", "Air conditioning", "City view", "Fast Wi-Fi", "Workspace"]),
        ]

        created_rooms = {}
        for hotel, name, ident, r_type, bed, view, bkfst, ac, quiet, price, cap, desc, a_names in room_records:
            room, _ = Room.objects.get_or_create(
                hotel=hotel,
                identifier=ident,
                defaults={
                    "name": name,
                    "room_type": r_type,
                    "bed_type": bed,
                    "view_type": view,
                    "has_breakfast": bkfst,
                    "has_ac": ac,
                    "is_quiet": quiet,
                    "price_per_night": Decimal(price),
                    "capacity": cap,
                    "description": desc,
                    "image_url": "/static/images/hero-hotel.png",
                }
            )
            # Ensure attributes match
            room.bed_type = bed
            room.view_type = view
            room.has_breakfast = bkfst
            room.has_ac = ac
            room.is_quiet = quiet
            room.price_per_night = Decimal(price)
            room.capacity = cap
            room.save()
            room.amenities.set([amenities[n] for n in a_names if n in amenities])
            hotel.amenities.add(*[amenities[n] for n in a_names if n in amenities])
            created_rooms[ident] = room

        # 4. Provision at least 10 Test Users (Target from Chapters 1-4)
        test_user_data = [
            ("emmanuel", "Emmanuel", "Nzeyimana", "emmanuel@example.com", "Ruyenzi", "deluxe", "double", "hill", True, True, True, Decimal("50.00"), 2, "TR5-DLX-01"),
            ("aline", "Aline", "Mukamana", "aline@example.com", "Ruyenzi", "standard", "single", "garden", True, True, True, Decimal("35.00"), 1, "TR5-STD-01"),
            ("jean", "Jean-Paul", "Habimana", "jean@example.com", "Ruyenzi", "suite", "king", "hill", True, True, True, Decimal("75.00"), 2, "TR5-STE-01"),
            ("clarisse", "Clarisse", "Uwase", "clarisse@example.com", "Kigali", "deluxe", "king", "city", True, True, True, Decimal("95.00"), 2, "KGL-KNG-01"),
            ("eric", "Eric", "Mugisha", "eric@example.com", "Ruyenzi", "standard", "twin", "garden", True, True, True, Decimal("45.00"), 2, "TR5-TWN-01"),
            ("sandrine", "Sandrine", "Gasana", "sandrine@example.com", "Kigali", "standard", "double", "garden", True, True, True, Decimal("60.00"), 2, "KGL-DBL-01"),
            ("claude", "Claude", "Nshimiyimana", "claude@example.com", "Ruyenzi", "family", "queen", "courtyard", True, True, True, Decimal("70.00"), 4, "TR5-FAM-01"),
            ("nadine", "Nadine", "Ingabire", "nadine@example.com", "Kigali", "suite", "queen", "garden", True, True, True, Decimal("95.00"), 2, "INZ-STE-01"),
            ("david", "David", "Rukundo", "david@example.com", "Ruyenzi", "deluxe", "double", "hill", True, True, True, Decimal("50.00"), 2, "TR5-DLX-01"),
            ("esperance", "Esperance", "Mukantwari", "esperance@example.com", "Ruyenzi", "suite", "king", "hill", True, True, True, Decimal("80.00"), 2, "TR5-STE-01"),
        ]

        today = timezone.localdate()
        for idx, (uname, fname, lname, email, city, rtype, bed, view, bkfst, ac, quiet, budget, guests, target_room_id) in enumerate(test_user_data):
            user, created = User.objects.get_or_create(
                username=uname,
                defaults={"first_name": fname, "last_name": lname, "email": email}
            )
            user.set_password("Guest@12345")
            user.first_name = fname
            user.last_name = lname
            user.email = email
            user.save()

            # Create or update Preferences matching the 6 stated criteria
            pref, _ = UserPreference.objects.get_or_create(user=user)
            pref.preferred_city = city
            pref.preferred_room_type = rtype
            pref.preferred_bed_type = bed
            pref.preferred_view = view
            pref.requires_breakfast = bkfst
            pref.requires_ac = ac
            pref.requires_quiet = quiet
            pref.max_price = budget
            pref.guests = guests
            pref.ai_travel_vibe = "peaceful scenic stay"
            pref.save()

            # Seed a booking for each user with upcoming check-in dates
            target_room = created_rooms.get(target_room_id)
            if target_room:
                check_in = today + timedelta(days=2 + idx * 3)
                check_out = check_in + timedelta(days=2)
                # Check if overlap exists before creating
                if not Booking.objects.filter(room=target_room, status="confirmed", check_in__lt=check_out, check_out__gt=check_in).exists():
                    booking = Booking(
                        user=user,
                        room=target_room,
                        check_in=check_in,
                        check_out=check_out,
                        guests=min(guests, target_room.capacity),
                        status="confirmed",
                    )
                    booking.save()

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded TR5 Hotel in Ruyenzi, Kigali partner hotels, {len(created_rooms)} rooms, and {len(test_user_data)} test users."
        ))
