# myapp/admin.py
from django.contrib import admin
from .models import (
    Tourist, APIKey, AuditLog, OTP, AadhaarOTP,
    TouristLocation, Itinerary, Trip, Cluster, ClusterMember
)

# ─── Tourist ────────────────────────────────────────────────
@admin.register(Tourist)
class TouristAdmin(admin.ModelAdmin):
    list_display = ('userid', 'name', 'email', 'mobile_no', 'is_mobile_verified', 'email_verified', 'aadhaar_verified', 'created_at')
    list_filter = ('is_mobile_verified', 'email_verified', 'aadhaar_verified', 'gender', 'blood_group')
    search_fields = ('userid', 'name', 'email', 'mobile_no', 'aadhaar_no', 'passport_no')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('userid', 'name', 'email', 'gender', 'dob', 'blood_group', 'mobile_no', 'emergency_contact')}),
        ('Verification', {'fields': ('is_mobile_verified', 'email_verified', 'aadhaar_verified', 'aadhaar_no', 'passport_no')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )

# ─── API Key ───────────────────────────────────────────────
@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at')
    search_fields = ('user__userid', 'key')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

# ─── Audit Log ─────────────────────────────────────────────
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'details')
    list_filter = ('action',)
    search_fields = ('user__userid', 'action', 'details')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

# ─── OTP ──────────────────────────────────────────────────
@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('tourist', 'code', 'type', 'created_at', 'expires_at', 'is_used')
    list_filter = ('type', 'is_used')
    search_fields = ('tourist__userid', 'code')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

# ─── Aadhaar OTP ──────────────────────────────────────────
@admin.register(AadhaarOTP)
class AadhaarOTPAdmin(admin.ModelAdmin):
    list_display = ('tourist', 'txn_id', 'otp_sent_at', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('tourist__userid', 'txn_id')
    readonly_fields = ('otp_sent_at',)
    ordering = ('-otp_sent_at',)

# ─── Tourist Location ─────────────────────────────────────
@admin.register(TouristLocation)
class TouristLocationAdmin(admin.ModelAdmin):
    list_display = ('tourist', 'latitude', 'longitude', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('tourist__userid',)
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)

# ─── Itinerary ────────────────────────────────────────────
class TripInline(admin.TabularInline):
    model = Trip
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ('title', 'tourist', 'start_date', 'end_date', 'base_location', 'created_at')
    list_filter = ('start_date', 'end_date')
    search_fields = ('title', 'tourist__userid', 'base_location')
    readonly_fields = ('created_at',)
    ordering = ('-start_date',)
    inlines = [TripInline]

# ─── Trip ─────────────────────────────────────────────────
@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('trip_title', 'itinerary', 'start_location', 'end_location', 'start_time', 'end_time', 'created_at')
    list_filter = ('start_time', 'end_time')
    search_fields = ('trip_title', 'itinerary__title', 'start_location', 'end_location')
    readonly_fields = ('created_at',)
    ordering = ('-start_time',)

# ─── Cluster ──────────────────────────────────────────────
class ClusterMemberInline(admin.TabularInline):
    model = ClusterMember
    extra = 0
    readonly_fields = ('location',)

@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ('cluster_id', 'center_latitude', 'center_longitude', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('cluster_id',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    inlines = [ClusterMemberInline]

# ─── Cluster Member ───────────────────────────────────────
@admin.register(ClusterMember)
class ClusterMemberAdmin(admin.ModelAdmin):
    list_display = ('cluster', 'location', 'get_tourist',)
    search_fields = ('cluster__cluster_id', 'location__tourist__userid')
    readonly_fields = ()
    ordering = ('cluster',)

    def get_tourist(self, obj):
        return obj.location.tourist.userid
    get_tourist.short_description = 'Tourist ID'
