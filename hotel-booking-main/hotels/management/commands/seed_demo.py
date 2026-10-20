from django.core.management.base import BaseCommand
from hotels.models import Amenity, Hotel, Room

class Command(BaseCommand):
    help = "Create a small set of demonstration hotels and rooms"

    def handle(self, *args, **options):
        amenities = {}
        for name, icon in [("Fast Wi-Fi", "bi-wifi"), ("Breakfast", "bi-cup-hot"), ("Pool", "bi-water"), ("Spa", "bi-flower1"), ("Ocean view", "bi-water"), ("Workspace", "bi-laptop")]:
            amenities[name], _ = Amenity.objects.get_or_create(name=name, defaults={"icon": icon})
        records = [
            ("The Verdant House", "Kigali", "Rwanda", "A serene urban retreat where considered design meets warm Rwandan hospitality.", "14 Palm Avenue, Kigali", "4.9", "Garden Suite", "suite", "A light-filled suite with a private lounge and garden outlook.", "185", 2, ["Fast Wi-Fi", "Breakfast", "Spa"]),
            ("Sea Glass Retreat", "Zanzibar", "Tanzania", "A quiet coastal hideaway shaped by sea air, natural textures, and unhurried days.", "Nungwi Coast, Zanzibar", "4.8", "Ocean Deluxe", "deluxe", "A calming room with generous proportions and views toward the water.", "240", 2, ["Ocean view", "Pool", "Breakfast"]),
            ("Canopy & Clay", "Nairobi", "Kenya", "Contemporary comfort surrounded by gardens in the heart of the city.", "Karura Lane, Nairobi", "4.7", "Canopy King", "standard", "A refined king room designed for restorative nights and productive mornings.", "145", 2, ["Fast Wi-Fi", "Workspace", "Breakfast"]),
        ]
        for name, city, country, description, address, rating, room_name, room_type, room_desc, price, capacity, amenity_names in records:
            hotel, _ = Hotel.objects.get_or_create(name=name, defaults={"city":city,"country":country,"description":description,"address":address,"rating":rating,"featured":True,"image_url":"/static/images/hero-hotel.png"})
            room, _ = Room.objects.get_or_create(hotel=hotel, name=room_name, defaults={"identifier":f"{city[:3].upper()}-{room_type[:3].upper()}-01","room_type":room_type,"description":room_desc,"price_per_night":price,"capacity":capacity,"image_url":"/static/images/hero-hotel.png"})
            room.amenities.set([amenities[n] for n in amenity_names]); hotel.amenities.add(*[amenities[n] for n in amenity_names])
        self.stdout.write(self.style.SUCCESS("Demo hotels and rooms are ready."))
