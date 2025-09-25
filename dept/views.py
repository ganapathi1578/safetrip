from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import PoliceOfficerRegistrationForm, PoliceOfficerLoginForm
from .models import PoliceOfficer
from django.shortcuts import render, redirect
from .forms import ZoneForm, ZoneTypeForm, ZoneAlertForm
from .models import Zone, ZoneType, ZoneAlert
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_GET


def register_view(request):
    if request.method == "POST":
        form = PoliceOfficerRegistrationForm(request.POST)
        if form.is_valid():
            officer = form.save(commit=False)
            officer.save()
            messages.success(request, "Registration successful! You can now log in.")
            return redirect("login")
    else:
        form = PoliceOfficerRegistrationForm()
    return render(request, "dept/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = PoliceOfficerLoginForm(request.POST)
        if form.is_valid():
            police_id = form.cleaned_data["police_id"]
            password = form.cleaned_data["password"]

            try:
                officer = PoliceOfficer.objects.get(police_id=police_id)
            except PoliceOfficer.DoesNotExist:
                officer = None

            if officer and officer.check_password(password):
                # Store officer ID in session
                request.session["police_officer_id"] = officer.id
                messages.success(request, f"Welcome {officer.name}!")
                return redirect("home")
            else:
                messages.error(request, "Invalid Police ID or password.")
    else:
        form = PoliceOfficerLoginForm()
    return render(request, "dept/login.html", {"form": form})

def logout_view(request):
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect("login")



def home_view(request):
    return render(request, "base.html")

from django.shortcuts import render, redirect
from django.contrib import messages
from django.forms import formset_factory
from django.views.decorators.http import require_http_methods

from .forms import ZoneForm, ZoneTypeFormSet, ZoneAlertFormSet
from .models import Zone, ZoneType, ZoneAlert
from django.db import transaction
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"])
def add_zone(request):
    """
    Single page to create Zone + multiple ZoneTypes + multiple ZoneAlerts (per type).
    Client JS keeps type_index on each alert so alerts can be associated with types.
    """
    if request.method == "POST":
        zone_form = ZoneForm(request.POST, prefix="zone")
        types_formset = ZoneTypeFormSet(request.POST, prefix="types")
        alerts_formset = ZoneAlertFormSet(request.POST, prefix="alerts")

        # debug helpers - if invalid, include the errors in messages to help debugging
        is_valid = zone_form.is_valid() and types_formset.is_valid() and alerts_formset.is_valid()
        if not is_valid:
            # Provide useful error output for debugging in dev — remove/adjust in production
            if not zone_form.is_valid():
                messages.error(request, f"Zone form errors: {zone_form.errors}")
            if not types_formset.is_valid():
                # formset.non_form_errors may include management_form problems
                messages.error(request, f"Types formset non-form errors: {types_formset.non_form_errors()}; forms errors: {[f.errors for f in types_formset]}")
            if not alerts_formset.is_valid():
                messages.error(request, f"Alerts formset non-form errors: {alerts_formset.non_form_errors()}; forms errors: {[f.errors for f in alerts_formset]}")
            # Fall through to render form with validation error messages shown in template
        else:
            # All valid -> perform DB writes inside a transaction
            try:
                with transaction.atomic():
                    zone = zone_form.save()

                    # Create ZoneType objects and map form-index -> ZoneType instance
                    type_map = {}
                    # types_formset.cleaned_data is a list ordered by form index (0..TOTAL_FORMS-1)
                    for form_index, tdata in enumerate(types_formset.cleaned_data):
                        # Cleaned data may contain empty dicts for entirely-empty extra forms
                        if not tdata:
                            continue
                        # If the form was marked for deletion, skip it
                        if tdata.get("DELETE", False):
                            continue
                        # Get the name (or other fields) and create model
                        name = tdata.get("name")
                        if not name:
                            # skip blank names to be safe
                            continue
                        zt = ZoneType.objects.create(zone=zone, name=name)
                        type_map[form_index] = zt

                    # Create ZoneAlert objects and attach them to the right ZoneType
                    for adata in alerts_formset.cleaned_data:
                        if not adata:
                            continue
                        if adata.get("DELETE", False):
                            continue
                        # type_index should be provided by your client JS
                        type_index = adata.get("type_index")
                        if type_index is None:
                            # skip alerts with no mapping (or you could raise/log)
                            continue
                        # ensure it's an int (sometimes comes as string)
                        try:
                            type_index = int(type_index)
                        except (ValueError, TypeError):
                            continue
                        zt = type_map.get(type_index)
                        if zt is None:
                            # alert refers to a type that was deleted or doesn't exist - skip
                            continue

                        # Create ZoneAlert (adjust fields if your model has different names)
                        ZoneAlert.objects.create(
                            zone_type=zt,
                            start_time=adata.get("start_time"),
                            end_time=adata.get("end_time"),
                            risk_points=adata.get("risk_points"),
                        )

                messages.success(request, "Zone, types and alerts saved successfully.")
                return redirect("add_zone")
            except Exception as e:
                # Rollback is automatic because of transaction.atomic(); show error for debugging
                messages.error(request, f"An error occurred while saving: {e}")

    else:
        zone_form = ZoneForm(prefix="zone")
        types_formset = ZoneTypeFormSet(prefix="types")
        alerts_formset = ZoneAlertFormSet(prefix="alerts")  # initially empty

    context = {
        "zone_form": zone_form,
        "types_formset": types_formset,
        "alerts_formset": alerts_formset,
    }
    return render(request, "dept/add_zone.html", context)



@require_GET
def zones_json(request):
    """
    Return all zones (id, name, lat, lng, radius, summary fields).
    """
    qs = Zone.objects.all()
    zones = []
    for z in qs:
        zones.append({
            "id": z.id,
            "name": z.name,
            "latitude": z.latitude,
            "longitude": z.longitude,
            "radius": float(z.radius) if z.radius is not None else None,
            "types_count": z.zone_types.count(),
        })
    return JsonResponse({"zones": zones})



@require_GET
def zone_detail_json(request, zone_id):
    """
    Return full details for a single zone: zone fields + types + alerts for each type.
    """
    try:
        z = Zone.objects.get(pk=zone_id)
    except Zone.DoesNotExist:
        raise Http404("Zone not found")

    types = []
    for t in z.zone_types.all():
        alerts = []
        for a in t.alerts.all():
            alerts.append({
                "id": a.id,
                "start_time": a.start_time.strftime("%H:%M"),
                "end_time": a.end_time.strftime("%H:%M"),
                "risk_points": a.risk_points,
            })
        types.append({
            "id": t.userid,
            "name": t.name,
            "alerts": alerts
        })

    payload = {
        "id": z.id,
        "name": z.name,
        "latitude": z.latitude,
        "longitude": z.longitude,
        "radius": float(z.radius) if z.radius is not None else None,
        "types": types,
    }
    return JsonResponse(payload)




######
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import OuterRef, Subquery, Max
from django.db.models.functions import Cast
from django.db.models import TimeField

from .models import Zone, ZoneType, ZoneAlert
from tourist.models import Tourist, TouristLocation

import datetime

# Utility to parse HH:MM time strings
def parse_time_str(tstr):
    try:
        return datetime.datetime.strptime(tstr, "%H:%M").time()
    except Exception:
        return None


def safetour_map(request):
    # Renders the HTML template — map + controls
    return render(request, "dept/home.html")


def api_filter_options(request):
    """Return available filter options: zone_types and distinct alert time windows.
    JSON structure:
    {"zone_types": [{"id":.., "name":.., "zone_id":.., "zone_name":..}],
     "time_windows": [{"start_time":"HH:MM", "end_time":"HH:MM"}] }
    """
    zone_types_qs = ZoneType.objects.select_related("zone").all()
    zone_types = [
        {"id": zt.id, "name": zt.name, "zone_id": zt.zone.id, "zone_name": zt.zone.name}
        for zt in zone_types_qs
    ]

    # List distinct time windows from ZoneAlert
    tw_qs = ZoneAlert.objects.values("start_time", "end_time").distinct()
    time_windows = [
        {"start_time": t["start_time"].strftime("%H:%M"), "end_time": t["end_time"].strftime("%H:%M")} for t in tw_qs
    ]

    return JsonResponse({"zone_types": zone_types, "time_windows": time_windows})


def api_alerts(request):
    """Return alerts filtered by zone_type ids and time filters.

    Query params (GET):
      - zone_type_ids: comma-separated ids (optional)
      - mode: 'current'|'all'|'custom' (default 'current')
      - start_time, end_time : used when mode=custom (format HH:MM)
      - include_latest_tourists: '1' or '0' (optional) — if set, the response will include a `latest_tourists` list

    Response structure:
      {"alerts": [ {id, zone_type: {id,name}, zone: {id,name,lat,lng,radius}, start_time, end_time, risk_points} ],
       "latest_tourists": [{tourist_id, name, latitude, longitude, timestamp}] }
    """
    zone_type_ids = request.GET.get("zone_type_ids")
    mode = request.GET.get("mode", "current")
    include_tourists = request.GET.get("include_latest_tourists", "0") == "1"

    alerts_qs = ZoneAlert.objects.select_related("zone_type", "zone_type__zone").all()

    if zone_type_ids:
        try:
            ids = [int(x) for x in zone_type_ids.split(",") if x.strip()]
            alerts_qs = alerts_qs.filter(zone_type__id__in=ids)
        except ValueError:
            pass

    now = timezone.localtime()

    if mode == "current":
        now_t = now.time()
        # filter alerts whose time window includes current time
        alerts_qs = alerts_qs.filter(start_time__lte=now_t, end_time__gte=now_t)
    elif mode == "custom":
        start = parse_time_str(request.GET.get("start_time", ""))
        end = parse_time_str(request.GET.get("end_time", ""))
        if start and end:
            # include if windows overlap: (a.start <= b.end) and (a.end >= b.start)
            alerts_qs = alerts_qs.filter(start_time__lte=end, end_time__gte=start)
    elif mode == "all":
        # no additional time filter
        pass

    alerts = []
    for a in alerts_qs.order_by("zone_type__zone__name", "start_time"):
        alerts.append({
            "id": a.id,
            "zone_type": {"id": a.zone_type.id, "name": a.zone_type.name},
            "zone": {
                "id": a.zone_type.zone.id,
                "name": a.zone_type.zone.name,
                "latitude": a.zone_type.zone.latitude,
                "longitude": a.zone_type.zone.longitude,
                "radius": a.zone_type.zone.radius,
            },
            "start_time": a.start_time.strftime("%H:%M"),
            "end_time": a.end_time.strftime("%H:%M"),
            "risk_points": a.risk_points,
        })
    #print(alerts)
    response = {"alerts": alerts}

    if include_tourists:
        # latest location per tourist
        latest_ts = TouristLocation.objects.filter(tourist=OuterRef("pk")).order_by("-timestamp")
        annot = Tourist.objects.annotate(latest_lat=Subquery(latest_ts.values("latitude")[:1]),
                                          latest_lng=Subquery(latest_ts.values("longitude")[:1]),
                                          latest_time=Subquery(latest_ts.values("timestamp")[:1]))
        tourists = []
        for t in annot:
            if t.latest_lat and t.latest_lng:
                tourists.append({
                    "tourist_id": t.userid,
                    "name": t.name,
                    "latitude": float(t.latest_lat),
                    "longitude": float(t.latest_lng),
                    "timestamp": t.latest_time.isoformat() if t.latest_time else None,
                })
        response["latest_tourists"] = tourists

    return JsonResponse(response)


def api_tourists_latest(request):
    """Return latest location per tourist. Useful for showing current positions on the map.

    Optional query params: none (could add pagination)
    """
    latest_ts = TouristLocation.objects.filter(tourist=OuterRef("pk")).order_by("-timestamp")
    annot = Tourist.objects.annotate(latest_lat=Subquery(latest_ts.values("latitude")[:1]),
                                      latest_lng=Subquery(latest_ts.values("longitude")[:1]),
                                      latest_time=Subquery(latest_ts.values("timestamp")[:1]))

    tourists = []
    for t in annot:
        if t.latest_lat and t.latest_lng:
            tourists.append({
                "tourist_id": t.userid,
                "userid": t.userid,
                "name": t.name,
                "latitude": float(t.latest_lat),
                "longitude": float(t.latest_lng),
                "timestamp": t.latest_time.isoformat() if t.latest_time else None,
            })
    return JsonResponse({"tourists": tourists})



# views.py
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.shortcuts import get_object_or_404

from tourist.models import Tourist, Itinerary


@require_GET
def get_tourist_details(request,userid):
    """
    Return tourist details, current itinerary (if any), and trips under that itinerary.
    """

    # fetch tourist or 404
    tourist = get_object_or_404(Tourist, userid=userid)

    # check for current itinerary
    today = timezone.now().date()
    current_itinerary = (
        Itinerary.objects
        .filter(tourist=tourist, start_date__lte=today, end_date__gte=today)
        .order_by("-created_at")
        .first()
    )

    # prepare response
    data = {
        "tourist": {
            "userid": tourist.userid,
            "name": tourist.name,
            "email": tourist.email,
            "gender": tourist.gender,
            "dob": str(tourist.dob) if tourist.dob else None,
            "blood_group": tourist.blood_group,
            "mobile_no": tourist.mobile_no,
            "is_mobile_verified": tourist.is_mobile_verified,
            "email_verified": tourist.email_verified,
            "aadhaar_no": tourist.aadhaar_no,
            "aadhaar_verified": tourist.aadhaar_verified,
            "passport_no": tourist.passport_no,
            "emergency_contact": tourist.emergency_contact,
            "created_at": tourist.created_at.isoformat(),
        },
        "current_itinerary": None,
        "trips": [],
    }

    if current_itinerary:
        data["current_itinerary"] = {
            "title": current_itinerary.title,
            "start_date": str(current_itinerary.start_date),
            "end_date": str(current_itinerary.end_date),
            "base_location": current_itinerary.base_location,
            "created_at": current_itinerary.created_at.isoformat(),
        }
        # include trips
        data["trips"] = [
            {
                "trip_title": trip.trip_title,
                "start_location": trip.start_location,
                "end_location": trip.end_location,
                "start_time": trip.start_time.isoformat(),
                "end_time": trip.end_time.isoformat(),
                "created_at": trip.created_at.isoformat(),
            }
            for trip in current_itinerary.trips.all().order_by("start_time")
        ]

    return JsonResponse(data, safe=False)

def tourist_map_view(request,tourist_id):
    #tourist_id = request.GET.get('tourist_id')
    tourist = None
    locations = []

    if tourist_id:
        tourist = get_object_or_404(Tourist, userid=tourist_id)
        locations_qs = TouristLocation.objects.filter(tourist=tourist).order_by('timestamp')
        locations = [
            {"lat": float(loc.latitude), "lng": float(loc.longitude), "timestamp": loc.timestamp.isoformat()}
            for loc in locations_qs
        ]

    return render(request, "dept/tourist_map.html", {
        "tourist_id": tourist_id,
        "locations": locations
    })



from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.db.models import OuterRef, Subquery
from tourist.models import Tourist, TouristLocation
from tourist.models import Cluster, ClusterMember
import datetime

@require_GET
def api_clusters(request):
    """
    Return clusters with their members and also latest tourists who are NOT in any cluster.
    Query params:
      - mode: 'current'|'all'|'custom' (optional) — currently forwarded but not used to filter clusters.
      - start_time, end_time for custom (not used here but accepted)
    Response:
    {
      "clusters": [
        {
          "cluster_id": int,
          "center_latitude": float,
          "center_longitude": float,
          "created_at": "iso",
          "members": [
            {"tourist_id": "...", "name": "...", "latitude": float, "longitude": float, "timestamp": "iso"}
          ]
        }, ...
      ],
      "unclustered_tourists": [
         {"tourist_id": "...", "name":"...", "latitude": float, "longitude": float, "timestamp":"iso"}
      ]
    }
    """
    # Fetch clusters and members
    clusters = []
    # Prefetch related objects to reduce DB hits
    qs = Cluster.objects.prefetch_related("members__location__tourist").order_by("-created_at")
    cluster_member_tourist_ids = set()

    for c in qs:
        members = []
        for cm in c.members.all():
            loc = cm.location
            if not loc:
                continue
            t = getattr(loc, 'tourist', None)
            tourist_id = t.userid if t else None
            if tourist_id:
                cluster_member_tourist_ids.add(tourist_id)
            members.append({
                "tourist_id": tourist_id,
                "name": t.name if t else None,
                "latitude": float(loc.latitude),
                "longitude": float(loc.longitude),
                "timestamp": loc.timestamp.isoformat() if loc.timestamp else None,
            })
        clusters.append({
            "cluster_id": c.cluster_id,
            "center_latitude": float(c.center_latitude),
            "center_longitude": float(c.center_longitude),
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "members": members
        })

    # Build latest location per tourist (annotate)
    latest_ts = TouristLocation.objects.filter(tourist=OuterRef("pk")).order_by("-timestamp")
    annot = Tourist.objects.annotate(
        latest_lat=Subquery(latest_ts.values("latitude")[:1]),
        latest_lng=Subquery(latest_ts.values("longitude")[:1]),
        latest_time=Subquery(latest_ts.values("timestamp")[:1])
    )

    unclustered = []
    for t in annot:
        # skip if no latest location
        if not t.latest_lat or not t.latest_lng:
            continue
        # if tourist is part of cluster members, skip
        if t.userid in cluster_member_tourist_ids:
            continue
        unclustered.append({
            "tourist_id": t.userid,
            "name": t.name,
            "latitude": float(t.latest_lat),
            "longitude": float(t.latest_lng),
            "timestamp": t.latest_time.isoformat() if t.latest_time else None,
        })

    return JsonResponse({"clusters": clusters, "unclustered_tourists": unclustered})
