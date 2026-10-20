from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
import uuid

def generate_room_identifier():
    return "RM-" + uuid.uuid4().hex[:8].upper()

class Amenity(models.Model):
    name = models.CharField(max_length=80, unique=True)
    icon = models.CharField(max_length=40, default="bi-check2-circle")
    def __str__(self): return self.name
    class Meta: verbose_name_plural = "amenities"; ordering = ["name"]

class Hotel(models.Model):
    name = models.CharField(max_length=160)
    city = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100)
    description = models.TextField()
    address = models.CharField(max_length=255)
    rating = models.DecimalField(max_digits=2, decimal_places=1, validators=[MinValueValidator(0), MaxValueValidator(5)])
    image_url = models.URLField(blank=True)
    featured = models.BooleanField(default=False)
    amenities = models.ManyToManyField(Amenity, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name
    class Meta: ordering = ["-featured", "-rating", "name"]

class Room(models.Model):
    ROOM_TYPES = [("standard", "Standard"), ("deluxe", "Deluxe"), ("suite", "Suite"), ("family", "Family")]
    STATUS_CHOICES = [("available", "Available"), ("maintenance", "Maintenance"), ("inactive", "Inactive")]
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="rooms")
    identifier = models.CharField(max_length=40, unique=True, default=generate_room_identifier, help_text="Unique room number or inventory code")
    name = models.CharField(max_length=120)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    description = models.TextField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    capacity = models.PositiveSmallIntegerField(default=2, validators=[MinValueValidator(1)])
    image = models.ImageField(upload_to="rooms/%Y/%m/", blank=True)
    image_url = models.URLField(blank=True)
    amenities = models.ManyToManyField(Amenity, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="available", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    @property
    def active(self): return self.status == "available"
    @property
    def display_image(self): return self.image.url if self.image else self.image_url
    def __str__(self): return f"{self.hotel.name} · {self.name}"
    class Meta: ordering = ["price_per_night", "name"]; constraints = [models.UniqueConstraint(fields=["hotel", "identifier"], name="unique_hotel_room_identifier")]
