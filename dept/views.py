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

@require_http_methods(["GET", "POST"])
def add_zone(request):
    """
    Single page to create Zone + multiple ZoneTypes + multiple ZoneAlerts (per type).
    The client-side JS will keep type_index on each alert to associate alerts with types.
    """

    if request.method == "POST":
        zone_form = ZoneForm(request.POST, prefix="zone")
        types_formset = ZoneTypeFormSet(request.POST, prefix="types")
        alerts_formset = ZoneAlertFormSet(request.POST, prefix="alerts")

        # Validate all
        if zone_form.is_valid() and types_formset.is_valid() and alerts_formset.is_valid():
            # 1) Create Zone
            zone = zone_form.save()

            # 2) Create ZoneType objects and keep mapping from form-index -> ZoneType obj
            type_map = {}  # index -> ZoneType instance
            for idx, tform in enumerate(types_formset.cleaned_data):
                if not tform or tform.get("DELETE", False):
                    continue
                name = tform.get("name")
                description = tform.get("description")
                zt = ZoneType.objects.create(zone=zone, name=name, description=description)
                type_map[idx] = zt

            # 3) Create alerts linked to the right ZoneType based on type_index
            for aform in alerts_formset.cleaned_data:
                if not aform or aform.get("DELETE", False):
                    continue
                type_index = aform.get("type_index")
                # If the user added an alert for a deleted type, skip
                zt = type_map.get(type_index)
                if zt is None:
                    continue
                ZoneAlert.objects.create(
                    zone_type=zt,
                    start_time=aform.get("start_time"),
                    end_time=aform.get("end_time"),
                    risk_points=aform.get("risk_points"),
                )

            messages.success(request, "Zone, types and alerts saved successfully.")
            return redirect("add_zone")
        else:
            # show errors inline
            messages.error(request, "Please fix the errors below.")
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
            "id": t.id,
            "name": t.name,
            "description": t.description,
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
