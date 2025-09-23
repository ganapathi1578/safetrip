from django.contrib import admin
from .models import (
    Tourist, APIKey, AuditLog, OTP, AadhaarOTP,
    TouristLocation, Itinerary, Trip
)

@admin.register(Tourist)
class TouristAdmin(admin.ModelAdmin):
    list_display = ("userid", "name", "email", "mobile_no", "is_mobile_verified", "email_verified", "aadhaar_verified")
    search_fields = ("userid", "name", "email", "mobile_no")
    list_filter = ("is_mobile_verified", "email_verified", "aadhaar_verified", "created_at")
    ordering = ("-created_at",)


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("user", "key", "created_at")
    search_fields = ("user__userid", "key")
    readonly_fields = ("created_at",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "timestamp")
    search_fields = ("user__userid", "action")
    list_filter = ("action", "timestamp")
    ordering = ("-timestamp",)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("tourist", "code", "type", "created_at", "expires_at", "is_used")
    search_fields = ("tourist__userid", "code")
    list_filter = ("type", "is_used")
    ordering = ("-created_at",)


@admin.register(AadhaarOTP)
class AadhaarOTPAdmin(admin.ModelAdmin):
    list_display = ("tourist", "txn_id", "otp_sent_at", "is_verified")
    search_fields = ("tourist__userid", "txn_id")
    list_filter = ("is_verified", "otp_sent_at")
    ordering = ("-otp_sent_at",)


@admin.register(TouristLocation)
class TouristLocationAdmin(admin.ModelAdmin):
    list_display = ("tourist", "latitude", "longitude", "timestamp")
    search_fields = ("tourist__userid",)
    list_filter = ("timestamp",)
    ordering = ("-timestamp",)


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ("tourist", "title", "start_date", "end_date", "base_location", "created_at")
    search_fields = ("tourist__userid", "title", "base_location")
    list_filter = ("start_date", "end_date")
    ordering = ("-created_at",)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("itinerary", "trip_title", "start_location", "end_location", "start_time", "end_time", "created_at")
    search_fields = ("trip_title", "start_location", "end_location", "itinerary__title")
    list_filter = ("start_time", "end_time")
    ordering = ("-created_at",)
