from django.contrib import admin
from .models import PoliceOfficer


# -------------------------
# PoliceOfficer Admin
# -------------------------
@admin.register(PoliceOfficer)
class PoliceOfficerAdmin(admin.ModelAdmin):
    list_display = ("police_id", "name", "email", "mobile_no", "rank", "station")
    search_fields = ("police_id", "name", "email", "mobile_no")
    list_filter = ("rank", "station")
    ordering = ("police_id",)


from django.contrib import admin
from django.utils import timezone
from datetime import time

from .models import Zone, ZoneType, ZoneAlert, PoliceOfficer


# -------------------------
# Inline for ZoneAlert (edit alerts on ZoneType page)
# -------------------------
class ZoneAlertInline(admin.TabularInline):
    model = ZoneAlert
    extra = 1
    fields = ("start_time", "end_time", "risk_points")
    verbose_name = "Zone Alert"
    verbose_name_plural = "Zone Alerts"


# -------------------------
# Inline for ZoneType (edit types on Zone page)
# -------------------------
class ZoneTypeInline(admin.StackedInline):
    model = ZoneType
    extra = 1
    fields = ("name", "description")
    show_change_link = True  # allows jumping to full ZoneType edit page (where alerts inline exist)


# -------------------------
# Zone Admin
# -------------------------
@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude", "longitude", "radius", "current_risks")
    search_fields = ("name",)
    list_filter = ("radius",)
    ordering = ("name",)
    inlines = [ZoneTypeInline]

    def current_risks(self, obj):
        """
        Return a small summary of active risks at current time.
        Shows the highest active risk per ZoneType if multiple alerts overlap.
        Handles wrap-around intervals (start_time > end_time).
        Example output: "Crime:80; Flood:60"
        """
        now_t = timezone.localtime().time()

        def in_time_range(s, e, check):
            # s,e,check are datetime.time
            if s <= e:
                return s <= check <= e
            # wrap-around (e.g., 20:00 -> 06:00)
            return check >= s or check <= e

        active = {}
        # each ZoneType belongs to this zone via related_name 'zone_types'
        for zt in obj.zone_types.all():
            # find active alerts for this zone type
            max_risk = None
            for alert in zt.alerts.all():
                if in_time_range(alert.start_time, alert.end_time, now_t):
                    if max_risk is None or alert.risk_points > max_risk:
                        max_risk = alert.risk_points
            if max_risk is not None:
                active[zt.name] = max_risk

        if not active:
            return "No active alerts"
        # format nicely
        return "; ".join([f"{k}:{v}" for k, v in active.items()])

    current_risks.short_description = "Active risks (now)"


# -------------------------
# ZoneType Admin (edit alerts inline)
# -------------------------
@admin.register(ZoneType)
class ZoneTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "zone", "alerts_count")
    search_fields = ("name", "zone__name")
    list_filter = ("zone__name",)
    inlines = [ZoneAlertInline]

    def alerts_count(self, obj):
        return obj.alerts.count()

    alerts_count.short_description = "Alerts"


# -------------------------
# ZoneAlert Admin
# -------------------------
@admin.register(ZoneAlert)
class ZoneAlertAdmin(admin.ModelAdmin):
    list_display = ("zone_type", "zone_name", "start_time", "end_time", "risk_points")
    search_fields = ("zone_type__name", "zone_type__zone__name")
    list_filter = ("risk_points",)
    ordering = ("-risk_points", "start_time")

    def zone_name(self, obj):
        return obj.zone_type.zone.name

    zone_name.short_description = "Zone"


