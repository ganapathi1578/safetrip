from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import datetime
import secrets
from datetime import timedelta

# ─── Tourist ────────────────────────────────────────────────

class Tourist(models.Model):
    #profile_photo
    userid = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    mobile_no = models.CharField(max_length=15)
    is_mobile_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    aadhaar_no = models.CharField(max_length=12, blank=True, null=True)
    aadhaar_verified = models.BooleanField(default=False)
    passport_no = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.userid})"



# ─────────────────────────────────────────────────────────────────────────────
# 🔐 API Key Model
# ─────────────────────────────────────────────────────────────────────────────

class APIKey(models.Model):
    """
    Stores an API key associated with a Django user.
    Used for authenticating API requests.
    """
    user = models.OneToOneField(Tourist, on_delete=models.CASCADE, related_name='api_key')
    key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(default=datetime.now())

    def regenerate_key(self):
        """Generate a new API key for the user."""
        self.key = secrets.token_hex(20)
        self.save()

    def __str__(self):
        return f"{self.user.username}'s API Key"

class AuditLog(models.Model):
    user = models.ForeignKey(Tourist, on_delete=models.CASCADE, related_name="logs")
    action = models.CharField(max_length=100)  # e.g., "OTP_SENT", "OTP_VERIFIED"
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.userid} - {self.action} @ {self.timestamp}"


class OTP(models.Model):
    OTP_TYPE_CHOICES = (
        ('mobile', 'Mobile'),
        ('email', 'Email'),
    )
    tourist = models.ForeignKey(Tourist, on_delete=models.CASCADE, blank=True, null=True, related_name="otps")
    code = models.CharField(max_length=6)  # 6-digit OTP
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    type = models.CharField(max_length=10, choices=OTP_TYPE_CHOICES, default='mobile')

    def is_valid(self):
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"OTP {self.code} ({self.type}) for {self.tourist.userid}"




## AADHAAR OTP


class AadhaarOTP(models.Model):
    tourist = models.ForeignKey('Tourist', on_delete=models.CASCADE, related_name="aadhaar_otps")
    txn_id = models.CharField(max_length=100, unique=True)  # returned by Aadhaar API
    otp_sent_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_verified and timezone.now() < self.otp_sent_at + timedelta(minutes=5)

    def __str__(self):
        return f"Aadhaar OTP for {self.tourist.userid} txn:{self.txn_id}"


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