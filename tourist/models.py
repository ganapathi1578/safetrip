from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


# ─── Tourist ────────────────────────────────────────────────

class Tourist(models.Model):
    userid = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    #gender
    #date of birth 
    # blood
    mobile_no = models.CharField(max_length=15)
    aadhaar_no = models.CharField(max_length=12, blank=True, null=True)
    passport_no = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    password = models.CharField(max_length=128)  # hashed
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.name} ({self.userid})"


# ─── Tourist Location ───────────────────────────────────────

class TouristLocation(models.Model):
    tourist = models.ForeignKey(Tourist, on_delete=models.CASCADE, related_name="locations")
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.tourist.userid} @ ({self.latitude}, {self.longitude})"


# ─── Itinerary ──────────────────────────────────────────────
# Represents the full stay (start/end dates and main location)

class Itinerary(models.Model):
    tourist = models.ForeignKey(Tourist, on_delete=models.CASCADE, related_name="itineraries")
    title = models.CharField(max_length=100)  # e.g., "Goa Summer Vacation"
    start_date = models.DateField()
    end_date = models.DateField()
    # purpouse
    base_location = models.CharField(max_length=200)  # state/city/country of stay
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Itinerary {self.title} ({self.tourist.userid})"


# ─── Trip ───────────────────────────────────────────────────
# Represents smaller trips inside an itinerary

class Trip(models.Model):
    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name="trips")
    trip_title = models.CharField(max_length=100)  # e.g., "Manali Trek"
    start_location = models.CharField(max_length=200)
    end_location = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Trip {self.trip_title} ({self.itinerary.title})"
