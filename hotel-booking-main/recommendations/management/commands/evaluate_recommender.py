import json
from types import SimpleNamespace
from django.core.management.base import BaseCommand
from hotels.models import Room
from recommendations.models import UserPreference
from recommendations.services import evaluate_profiles

class Command(BaseCommand):
    help = "Evaluate deterministic top-3 coverage for saved preference profiles"
    def handle(self, *args, **options):
        profiles = list(UserPreference.objects.select_related("user").prefetch_related("amenities"))
        source = "saved"
        if not profiles:
            source = "synthetic"
            class EmptyAmenities:
                def values_list(self, *args, **kwargs): return []
            rooms = list(Room.objects.filter(status="available").select_related("hotel")[:3])
            profiles = [SimpleNamespace(user_id=f"sample-{i+1}", preferred_city=room.hotel.city, preferred_room_type=room.room_type, max_price=room.price_per_night, guests=min(room.capacity, 2), requested_check_in=None, requested_check_out=None, amenities=EmptyAmenities()) for i, room in enumerate(rooms)]
        report = evaluate_profiles(profiles); report["profile_source"] = source
        self.stdout.write(json.dumps(report, indent=2))
