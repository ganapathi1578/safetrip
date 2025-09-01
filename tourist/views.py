import random
from datetime import timedelta
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone

from .models import Tourist, Itinerary, Trip, TouristLocation

# A few Aizawl landmarks (approximate coords)
AIZAWL_PLACES = {
    "Treasury Square":  (23.7279, 92.7179),
    "Dawrpui":          (23.7299, 92.7196),
    "Zarkawt":          (23.7309, 92.7207),
    "Chanmari":         (23.7360, 92.7270),
    "Bawngkawn":        (23.7605, 92.7239),
    "Bethlehem Veng":   (23.7222, 92.7089),
    "Vaivakawn":        (23.7195, 92.7053),
    "Khatla":           (23.7247, 92.7162),
    "Durtlang":         (23.7880, 92.7305),
    "Hunthar":          (23.7350, 92.7245),
}

DEMO_NAMES = ["Riya", "Arun", "Meera", "Vikram", "Tashi", "Lalduhawmi", "Kima", "Ananya", "Rahul", "Pooja"]

def _jitter(lat, lon, scale=0.0012):
    """Small random jitter to avoid perfectly straight lines."""
    return lat + random.uniform(-scale, scale), lon + random.uniform(-scale, scale)

def _interp_points(start, end, steps=20, jitter_scale=0.0006):
    """Generate points from start->end with slight jitter."""
    (lat1, lon1), (lat2, lon2) = start, end
    pts = []
    for i in range(steps):
        t = i / (steps - 1)
        lat = lat1 + (lat2 - lat1) * t
        lon = lon1 + (lon2 - lon1) * t
        lat, lon = lat + random.uniform(-jitter_scale, jitter_scale), lon + random.uniform(-jitter_scale, jitter_scale)
        pts.append((round(lat, 6), round(lon, 6)))
    return pts

@transaction.atomic
def seed_aizawl_view(request):
    """
    Creates 5 demo tourists, each with:
      - 1 itinerary ("Aizawl Visit")
      - 5 trips between Aizawl localities
      - ~20 location pings per trip spaced by 5 minutes
    Safe-guard: only allowed in DEBUG or with ?key=letmein
    """
    # safety gate
    from django.conf import settings
    if not settings.DEBUG and request.GET.get("key") != "letmein":
        return HttpResponseForbidden("Forbidden in production. Add ?key=letmein to override (only for demo).")

    # wipe prior demo data to keep idempotent
    TouristLocation.objects.filter(tourist__userid__startswith="demo_T").delete()
    Trip.objects.filter(itinerary__tourist__userid__startswith="demo_T").delete()
    Itinerary.objects.filter(tourist__userid__startswith="demo_T").delete()
    Tourist.objects.filter(userid__startswith="demo_T").delete()

    created = []

    place_names = list(AIZAWL_PLACES.keys())
    now = timezone.now()

    for idx in range(1, 6):  # 5 tourists
        userid = f"demo_T{idx:03d}"
        name = random.choice(DEMO_NAMES)
        email = f"{userid.lower()}@example.com"
        mobile = f"9{random.randint(100000000, 999999999)}"

        tourist = Tourist.objects.create(
            userid=userid,
            name=name,
            email=email,
            mobile_no=mobile,
            password="demo_password_123",  # will be hashed by model.save()
            emergency_contact="9111111111",
        )

        # Itinerary: 5 days around Aizawl
        start_date = (now - timedelta(days=5)).date()
        end_date = (now + timedelta(days=1)).date()

        itinerary = Itinerary.objects.create(
            tourist=tourist,
            title="Aizawl Visit",
            start_date=start_date,
            end_date=end_date,
            base_location="Aizawl, Mizoram",
        )

        # Create 5 trips per tourist
        trip_base_time = now - timedelta(days=3)  # older trips start ~3 days ago

        for tnum in range(1, 6):
            start_name, end_name = random.sample(place_names, 2)
            start_coords = AIZAWL_PLACES[start_name]
            end_coords = AIZAWL_PLACES[end_name]

            start_time = trip_base_time + timedelta(hours=(tnum - 1) * 6)
            end_time = start_time + timedelta(hours=random.randint(1, 3))

            trip = Trip.objects.create(
                itinerary=itinerary,
                trip_title=f"Trip {tnum}: {start_name} → {end_name}",
                start_location=start_name,
                end_location=end_name,
                start_time=start_time,
                end_time=end_time,
            )

            # Generate ~20 pings along the path, 5 minutes apart
            points = _interp_points(start_coords, end_coords, steps=20)
            tstamp = start_time
            for lat, lon in points:
                # slight additional jitter so multiple users don't overlap perfectly
                jlat, jlon = _jitter(lat, lon, scale=0.0004)
                TouristLocation.objects.create(
                    tourist=tourist,
                    latitude=round(jlat, 6),
                    longitude=round(jlon, 6),
                    timestamp=tstamp,
                )
                tstamp += timedelta(minutes=5)

        created.append(userid)

    return JsonResponse({
        "status": "ok",
        "message": "Seeded demo Aizawl data.",
        "tourists_created": created,
        "trips_per_tourist": 5,
        "pings_per_trip": 20,
        "place_pool": place_names,
    })
