# admin.py
from django.contrib import admin
from .models import Tourist, TouristLocation, Itinerary, Trip


@admin.register(Tourist)
class TouristAdmin(admin.ModelAdmin):
    list_display = ("userid", "name", "email", "mobile_no", "aadhaar_no", "passport_no", "created_at")
    search_fields = ("userid", "name", "email", "mobile_no", "aadhaar_no", "passport_no")
    list_filter = ("created_at",)
    ordering = ("-created_at",)


@admin.register(TouristLocation)
class TouristLocationAdmin(admin.ModelAdmin):
    list_display = ("tourist", "latitude", "longitude", "timestamp")
    search_fields = ("tourist__userid", "tourist__name")
    list_filter = ("timestamp",)
    ordering = ("-timestamp",)


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ("title", "tourist", "start_date", "end_date", "base_location", "created_at")
    search_fields = ("title", "tourist__userid", "tourist__name", "base_location")
    list_filter = ("start_date", "end_date", "created_at")
    ordering = ("-created_at",)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("trip_title", "itinerary", "start_location", "end_location", "start_time", "end_time", "created_at")
    search_fields = ("trip_title", "itinerary__title", "start_location", "end_location")
    list_filter = ("start_time", "end_time", "created_at")
    ordering = ("-created_at",)
