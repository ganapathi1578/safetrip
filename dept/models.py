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
