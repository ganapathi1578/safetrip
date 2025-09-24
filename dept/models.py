import os
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class PoliceOfficer(models.Model):
    police_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile_no = models.CharField(max_length=15)
    rank = models.CharField(max_length=50, blank=True, null=True)
    station = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=128)  # store hashed password

    def save(self, *args, **kwargs):
        # Ensure password is hashed before saving
        if self.password and not self.password.startswith("pbkdf2_"):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        """Verify if a raw password matches the stored hash"""
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.name} ({self.police_id})"


from django.db import models

class Zone(models.Model):
    name = models.CharField(max_length=100)  # e.g., "Central Aizawl"
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius = models.FloatField(help_text="Radius in meters")

    def __str__(self):
        return self.name


class ZoneType(models.Model):
    # NOTE: ZoneType is now tied to a particular Zone (hierarchical)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name="zone_types")
    name = models.CharField(max_length=100)  # e.g., "Crime", "Flood", "Landslide"
    #description = models.TextField(blank=True, null=True)

    class Meta:
        # same type name can exist across different zones but keep unique per-zone
        unique_together = ("zone", "name")
        ordering = ("zone", "name")

    def __str__(self):
        return f"{self.name} — {self.zone.name}"


class ZoneAlert(models.Model):
    # now alert belongs to a ZoneType (which already knows the Zone)
    zone_type = models.ForeignKey(ZoneType, on_delete=models.CASCADE, related_name="alerts")

    # allow either time-of-day windows (TimeField) OR full datetime if needed later.
    start_time = models.TimeField()
    end_time = models.TimeField()
    risk_points = models.PositiveIntegerField(default=0, help_text="Risk score between 0 and 100")

    class Meta:
        ordering = ("zone_type", "start_time")

    def __str__(self):
        return f"{self.zone_type.zone.name} • {self.zone_type.name} ({self.start_time}-{self.end_time}) = {self.risk_points}"
