import random
from datetime import timedelta
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils import timezone
import random, secrets, hashlib, requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from .models import Tourist, OTP, APIKey, AuditLog
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Tourist, Itinerary, Trip, TouristLocation
from .decorators import require_api_key
from .models import AadhaarOTP
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from .models import Tourist, OTP
import random

# # A few Aizawl landmarks (approximate coords)
# AIZAWL_PLACES = {
#     "Treasury Square":  (23.7279, 92.7179),
#     "Dawrpui":          (23.7299, 92.7196),
#     "Zarkawt":          (23.7309, 92.7207),
#     "Chanmari":         (23.7360, 92.7270),
#     "Bawngkawn":        (23.7605, 92.7239),
#     "Bethlehem Veng":   (23.7222, 92.7089),
#     "Vaivakawn":        (23.7195, 92.7053),
#     "Khatla":           (23.7247, 92.7162),
#     "Durtlang":         (23.7880, 92.7305),
#     "Hunthar":          (23.7350, 92.7245),
# }

# DEMO_NAMES = ["Riya", "Arun", "Meera", "Vikram", "Tashi", "Lalduhawmi", "Kima", "Ananya", "Rahul", "Pooja"]

# def _jitter(lat, lon, scale=0.0012):
#     """Small random jitter to avoid perfectly straight lines."""
#     return lat + random.uniform(-scale, scale), lon + random.uniform(-scale, scale)

# def _interp_points(start, end, steps=20, jitter_scale=0.0006):
#     """Generate points from start->end with slight jitter."""
#     (lat1, lon1), (lat2, lon2) = start, end
#     pts = []
#     for i in range(steps):
#         t = i / (steps - 1)
#         lat = lat1 + (lat2 - lat1) * t
#         lon = lon1 + (lon2 - lon1) * t
#         lat, lon = lat + random.uniform(-jitter_scale, jitter_scale), lon + random.uniform(-jitter_scale, jitter_scale)
#         pts.append((round(lat, 6), round(lon, 6)))
#     return pts

# @transaction.atomic
# def seed_aizawl_view(request):
#     """
#     Creates 5 demo tourists, each with:
#       - 1 itinerary ("Aizawl Visit")
#       - 5 trips between Aizawl localities
#       - ~20 location pings per trip spaced by 5 minutes
#     Safe-guard: only allowed in DEBUG or with ?key=letmein
#     """
#     # safety gate
#     from django.conf import settings
#     if not settings.DEBUG and request.GET.get("key") != "letmein":
#         return HttpResponseForbidden("Forbidden in production. Add ?key=letmein to override (only for demo).")

#     # wipe prior demo data to keep idempotent
#     TouristLocation.objects.filter(tourist__userid__startswith="demo_T").delete()
#     Trip.objects.filter(itinerary__tourist__userid__startswith="demo_T").delete()
#     Itinerary.objects.filter(tourist__userid__startswith="demo_T").delete()
#     Tourist.objects.filter(userid__startswith="demo_T").delete()

#     created = []

#     place_names = list(AIZAWL_PLACES.keys())
#     now = timezone.now()

#     for idx in range(1, 6):  # 5 tourists
#         userid = f"demo_T{idx:03d}"
#         name = random.choice(DEMO_NAMES)
#         email = f"{userid.lower()}@example.com"
#         mobile = f"9{random.randint(100000000, 999999999)}"

#         tourist = Tourist.objects.create(
#             userid=userid,
#             name=name,
#             email=email,
#             mobile_no=mobile,
#             password="demo_password_123",  # will be hashed by model.save()
#             emergency_contact="9111111111",
#         )

#         # Itinerary: 5 days around Aizawl
#         start_date = (now - timedelta(days=5)).date()
#         end_date = (now + timedelta(days=1)).date()

#         itinerary = Itinerary.objects.create(
#             tourist=tourist,
#             title="Aizawl Visit",
#             start_date=start_date,
#             end_date=end_date,
#             base_location="Aizawl, Mizoram",
#         )

#         # Create 5 trips per tourist
#         trip_base_time = now - timedelta(days=3)  # older trips start ~3 days ago

#         for tnum in range(1, 6):
#             start_name, end_name = random.sample(place_names, 2)
#             start_coords = AIZAWL_PLACES[start_name]
#             end_coords = AIZAWL_PLACES[end_name]

#             start_time = trip_base_time + timedelta(hours=(tnum - 1) * 6)
#             end_time = start_time + timedelta(hours=random.randint(1, 3))

#             trip = Trip.objects.create(
#                 itinerary=itinerary,
#                 trip_title=f"Trip {tnum}: {start_name} → {end_name}",
#                 start_location=start_name,
#                 end_location=end_name,
#                 start_time=start_time,
#                 end_time=end_time,
#             )

#             # Generate ~20 pings along the path, 5 minutes apart
#             points = _interp_points(start_coords, end_coords, steps=20)
#             tstamp = start_time
#             for lat, lon in points:
#                 # slight additional jitter so multiple users don't overlap perfectly
#                 jlat, jlon = _jitter(lat, lon, scale=0.0004)
#                 TouristLocation.objects.create(
#                     tourist=tourist,
#                     latitude=round(jlat, 6),
#                     longitude=round(jlon, 6),
#                     timestamp=tstamp,
#                 )
#                 tstamp += timedelta(minutes=5)

#         created.append(userid)

#     return JsonResponse({
#         "status": "ok",
#         "message": "Seeded demo Aizawl data.",
#         "tourists_created": created,
#         "trips_per_tourist": 5,
#         "pings_per_trip": 20,
#         "place_pool": place_names,
#     })







# helper function
def send_otp_msg91(mobile, otp):
    """Send OTP via MSG91"""
    url = settings.MSG91_BASE_URL
    headers = {
        "accept": "application/json",
        "authkey": settings.MSG91_AUTH_KEY,
        "content-type": "application/json"
    }
    payload = {
        "template_id": settings.MSG91_TEMPLATE_ID,
        "short_url": "0",
        "recipients": [
            {"mobiles": f"91{mobile}", "otp": str(otp)}
        ]
    }
    #response = requests.post(url, json=payload, headers=headers)
    #return response.json()
    print(otp)
    return otp


@csrf_exempt
def request_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    data = json.loads(request.body.decode("utf-8"))
    mobile = data.get("mobile")

    if not mobile:
        return JsonResponse({"error": "Mobile number required"}, status=400)

    # Check if tourist exists, create if not
    tourist, _ = Tourist.objects.get_or_create(
        mobile_no=mobile,
        defaults={"userid": f"user_{secrets.token_hex(4)}", "name": "Pending Name"}
    )

    otp_code = random.randint(100000, 999999)
    expires_at = timezone.now() + timedelta(minutes=5)

    # store OTP in DB
    otp_obj = OTP.objects.create(
        tourist=tourist,
        code=str(otp_code),
        expires_at=expires_at
    )

    # create a session hash
    otp_hash = hashlib.sha256(f"{otp_obj.id}{otp_code}{secrets.token_hex(8)}".encode()).hexdigest()
    
    otp_obj.details = otp_hash
    otp_obj.save()

    # send OTP via MSG91
    send_response = send_otp_msg91(mobile, otp_code)

    # log in AuditLog
    AuditLog.objects.create(user=tourist, action="OTP_SENT", details=f"Mobile {mobile}")

    return JsonResponse({
        "hash": otp_hash,
        "status": "OTP sent"
    })


@csrf_exempt
def verify_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    data = json.loads(request.body.decode("utf-8"))
    otp_code = data.get("otp")
    otp_hash = data.get("hash")
    mobile = data.get("mobile")
    print(otp_code, otp_hash, mobile)
    if not otp_code or not otp_hash or not mobile:
        return JsonResponse({"error": "otp, hash, mobile required"}, status=400)

    # find OTP object
    otp_obj = OTP.objects.filter(code=otp_code, is_used=False).last()
    if not otp_obj or not otp_obj.is_valid():
        return JsonResponse({"error": "Invalid or expired OTP"}, status=400)

    # mark used
    otp_obj.is_used = True
    otp_obj.save()

    # get the tourist
    tourist = otp_obj.tourist
    tourist.is_mobile_verified = True
    tourist.save()

    # create or fetch API Key
    api_key, _ = APIKey.objects.get_or_create(user=tourist)
    if not api_key.key:
        api_key.regenerate_key()

    AuditLog.objects.create(user=tourist, action="OTP_VERIFIED")

    return JsonResponse({
        "status": "success",
        "user_id": tourist.userid,
        "api_key": api_key.key,
        "is_mobile_verified": tourist.is_mobile_verified,
        "is_email_verified": getattr(tourist, "email_verified", False),
        "is_aadhaar_verified": getattr(tourist, "aadhaar_verified", False)
    })





@csrf_exempt
@require_api_key
def send_aadhaar_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body.decode("utf-8"))
    aadhaar_number = data.get("aadhaar")
    if not aadhaar_number:
        return JsonResponse({"error": "Aadhaar number required"}, status=400)

    # Call Aadhaar API to send OTP (mock example)
    # aadhaar_api_url = "https://aadhaar-api.gov/send-otp"
    # payload = {"aadhaar": aadhaar_number}
    # # In reality, you’ll need API headers, keys, etc.
    # response = requests.post(aadhaar_api_url, json=payload).json()

    # txn_id = response.get("txnId")  # Aadhaar API returns txnId
    # if not txn_id:
    #     return JsonResponse({"error": "Failed to send OTP"}, status=500)
    print(aadhaar_number)
    txn_id = hashlib.sha256(f"{int(aadhaar_number)}".encode()).hexdigest()

    # Save in DB
    AadhaarOTP.objects.create(tourist=request.user, txn_id=txn_id)
    return JsonResponse({"status": "OTP sent", "txn_id": txn_id})



@csrf_exempt
@require_api_key
def verify_aadhaar_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body.decode("utf-8"))
    txn_id = data.get("txn_id")
    otp = data.get("otp")

    if not txn_id or not otp:
        return JsonResponse({"error": "txn_id and otp required"}, status=400)

    # Get OTP object
    try:
        aadhaar_otp = AadhaarOTP.objects.get(txn_id=txn_id, tourist=request.user)
    except AadhaarOTP.DoesNotExist:
        return JsonResponse({"error": "Invalid txn_id"}, status=404)

    if not aadhaar_otp.is_valid():
        return JsonResponse({"error": "OTP expired or already verified"}, status=400)

    # Call Aadhaar API to verify OTP (mock)
    # aadhaar_verify_url = "https://aadhaar-api.gov/verify-otp"
    # payload = {"txnId": txn_id, "otp": otp}
    # response = requests.post(aadhaar_verify_url, json=payload).json()

    # if not response.get("success"):
    #     return JsonResponse({"error": "OTP verification failed"}, status=400)

    # Mark OTP verified
    aadhaar_otp.is_verified = True
    aadhaar_otp.save()

    # Update Tourist details
    # details = response.get("aadhaar_details", {})
    tourist = request.user
    # tourist.name = details.get("name", tourist.name)
    # tourist.dob = details.get("dob", tourist.dob)
    # tourist.gender = details.get("gender", tourist.gender)
    # tourist.aadhaar_no = details.get("aadhaar_no", tourist.aadhaar_no)
    tourist.save()

    return JsonResponse({"status": "Aadhaar verified"})


# @csrf_exempt
# @require_api_key
# def verify_aadhaar_otp(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "POST only"}, status=405)

#     data = json.loads(request.body.decode("utf-8"))
#     txn_id = data.get("txn_id")
#     otp = data.get("otp")

#     if not txn_id or not otp:
#         return JsonResponse({"error": "txn_id and otp required"}, status=400)

#     # Get OTP object
#     try:
#         aadhaar_otp = AadhaarOTP.objects.get(txn_id=txn_id, tourist=request.user)
#     except AadhaarOTP.DoesNotExist:
#         return JsonResponse({"error": "Invalid txn_id"}, status=404)

#     if not aadhaar_otp.is_valid():
#         return JsonResponse({"error": "OTP expired or already verified"}, status=400)

#     # Call Aadhaar API to verify OTP (mock)
#     aadhaar_verify_url = "https://aadhaar-api.gov/verify-otp"
#     payload = {"txnId": txn_id, "otp": otp}
#     response = requests.post(aadhaar_verify_url, json=payload).json()

#     if not response.get("success"):
#         return JsonResponse({"error": "OTP verification failed"}, status=400)

#     # Mark OTP verified
#     aadhaar_otp.is_verified = True
#     aadhaar_otp.save()

#     # Update Tourist details
#     details = response.get("aadhaar_details", {})
#     tourist = request.user
#     tourist.name = details.get("name", tourist.name)
#     tourist.dob = details.get("dob", tourist.dob)
#     tourist.gender = details.get("gender", tourist.gender)
#     tourist.aadhaar_no = details.get("aadhaar_no", tourist.aadhaar_no)
#     tourist.save()

#     return JsonResponse({"status": "Aadhaar verified", "details": details})




## helper function
def send_email_otp(to_email, otp_code):
    subject = "Your OTP Verification Code"
    message = f"Your OTP code is: {otp_code}. It is valid for 5 minutes."
    send_mail(subject, message, settings.EMAIL_HOST_USER, [to_email])






@csrf_exempt
@require_api_key
def request_email_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body.decode("utf-8"))
    userid = data.get("user_id")
    email = data.get("email")

    if not userid or not email:
        return JsonResponse({"error": "User ID and Email are required"}, status=400)

    try:
        # Search for the tourist using the user_id string field
        tourist = Tourist.objects.get(userid=userid)
    except Tourist.DoesNotExist:
        return JsonResponse({"error": "Tourist not found"}, status=404)

    # Update the tourist's email address with the new email
    tourist.email = email
    tourist.save()

    otp_code = random.randint(100000, 999999)
    print(otp_code)
    expires_at = timezone.now() + timedelta(minutes=5)

    otp_obj = OTP.objects.create(
        tourist=tourist,
        code=str(otp_code),
        expires_at=expires_at,
        type='email'
    )

    send_email_otp(email, otp_code)
    return JsonResponse({"status": "OTP sent to email and user email updated"})


@csrf_exempt
@require_api_key
def verify_email_otp(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body.decode("utf-8"))
    userid = data.get("user_id")
    otp_code = data.get("otp")

    if not userid or not otp_code:
        return JsonResponse({"error": "User ID and OTP required"}, status=400)

    try:
        # Search for the tourist using the user_id string field
        tourist = Tourist.objects.get(userid=userid)
    except Tourist.DoesNotExist:
        return JsonResponse({"error": "Tourist not found"}, status=404)

    otp_obj = OTP.objects.filter(
        tourist=tourist,
        code=otp_code,
        type='email',
        is_used=False
    ).last()

    if not otp_obj or not otp_obj.is_valid():
        return JsonResponse({"error": "Invalid or expired OTP"}, status=400)

    otp_obj.is_used = True
    otp_obj.save()

    # Mark email as verified
    tourist.email_verified = True
    tourist.save()

    return JsonResponse({"status": "Email verified"})






@csrf_exempt
@require_api_key
def get_tourist_details(request):
    """
    Fetches a tourist's complete details by their user ID.
    This is a GET request.
    """
    if request.method != "GET":
        return JsonResponse({"error": "GET only"}, status=405)

    user_id = request.GET.get("user_id")
    if not user_id:
        return JsonResponse({"error": "User ID required"}, status=400)

    try:
        tourist = Tourist.objects.get(userid=user_id)
        # Serialize the tourist object to a dictionary
        details = {
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
        }
        return JsonResponse(details)
    except Tourist.DoesNotExist:
        return JsonResponse({"error": "Tourist not found"}, status=404)

@csrf_exempt
@require_api_key
def save_tourist_details(request):
    """
    Saves and updates a tourist's details.
    This is a POST request.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    data = json.loads(request.body.decode("utf-8"))
    user_id = data.get("user_id")
    if not user_id:
        return JsonResponse({"error": "User ID is required"}, status=400)

    try:
        tourist = Tourist.objects.get(userid=user_id)
        
        # Update editable fields
        tourist.name = data.get("name", tourist.name)
        tourist.gender = data.get("gender", tourist.gender)
        tourist.dob = data.get("dob") if data.get("dob") else tourist.dob
        tourist.blood_group = data.get("blood_group", tourist.blood_group)
        tourist.passport_no = data.get("passport_no", tourist.passport_no)
        tourist.emergency_contact = data.get("emergency_contact", tourist.emergency_contact)

        tourist.save()

        return JsonResponse({"status": "Details saved successfully"})
    except Tourist.DoesNotExist:
        return JsonResponse({"error": "Tourist not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
def save_tourist_location(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            userid = data.get("user_id")
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            timestamp = data.get("timestamp", timezone.now())

            if not userid or not latitude or not longitude:
                return JsonResponse({"error": "Missing required fields"}, status=400)

            # find the tourist
            tourist = get_object_or_404(Tourist, userid=userid)

            # save location
            location = TouristLocation.objects.create(
                tourist=tourist,
                latitude=latitude,
                longitude=longitude,
                timestamp=timestamp,
            )

            return JsonResponse({
                "status": "success",
                "id": location.id,
                "user_id": tourist.userid,
                "latitude": str(location.latitude),
                "longitude": str(location.longitude),
                "timestamp": location.timestamp.isoformat(),
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)