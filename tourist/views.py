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
from django.views.decorators.http import require_GET
# A few Aizawl landmarks (approximate coords)
# views.py (add to your app)
import random
import string
import secrets
from datetime import timedelta, datetime

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.http import require_GET

# adjust this import to match your app layout
from .models import (
    Tourist, APIKey, AuditLog, OTP, AadhaarOTP,
    TouristLocation, Itinerary, Trip
)


# Sample Aizawl places used to generate locations
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

FIRST_NAMES = ["Riya", "Arun", "Meera", "Vikram", "Tashi", "Lalduhawmi", "Kima", "Ananya", "Rahul", "Pooja", "Sangma", "Lalruatfela"]
GENDERS = ["male", "female", "other"]
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

def _random_dob(min_age=18, max_age=65):
    """Return a date object for a random DOB between min_age and max_age."""
    today = timezone.now().date()
    start_year = today.year - max_age
    end_year = today.year - min_age
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    # pick a safe day for the month
    day = random.randint(1, 28)
    return datetime(year, month, day).date()

def _random_aadhaar():
    """Return a 12-digit Aadhaar-like string (not real)."""
    return ''.join(str(random.randint(0, 9)) for _ in range(12))

def _random_passport():
    """Return a pseudo passport number: 1 letter + 7 digits."""
    return random.choice(string.ascii_uppercase) + ''.join(random.choice(string.digits) for _ in range(7))

def _random_mobile():
    """Return a 10-digit mobile number starting with 7/8/9 (India style)."""
    return random.choice(["7","8","9"]) + ''.join(random.choice(string.digits) for _ in range(9))

def _jitter(lat, lon, scale=0.0009):
    """Small jitter to avoid perfectly overlapping points."""
    return lat + random.uniform(-scale, scale), lon + random.uniform(-scale, scale)

@require_GET
@transaction.atomic
def seed_aizawl_demo(request):
    """
    Seed 10 demo tourists and fill all model fields:
      - Tourist (userid, name, email, dob, gender, blood_group, mobile_no, is_mobile_verified, email_verified,
                 aadhaar_no, aadhaar_verified, passport_no, emergency_contact, created_at)
      - APIKey
      - AuditLog entries
      - OTP (mobile/email)
      - AadhaarOTP
      - Itinerary, Trip (small number)
      - 30 TouristLocation pings (5 minutes apart), recent (ending at now)
    Safety: only in DEBUG or with ?key=letmein
    """
    # safety gate
    if not settings.DEBUG and request.GET.get("key") != "letmein":
        return HttpResponseForbidden("Forbidden in production. Use DEBUG or ?key=letmein in dev.")

    # wipe previous demo data
    TouristLocation.objects.filter(tourist__userid__startswith="demo_T").delete()
    Trip.objects.filter(itinerary__tourist__userid__startswith="demo_T").delete()
    Itinerary.objects.filter(tourist__userid__startswith="demo_T").delete()
    OTP.objects.filter(tourist__userid__startswith="demo_T").delete()
    AadhaarOTP.objects.filter(tourist__userid__startswith="demo_T").delete()
    AuditLog.objects.filter(user__userid__startswith="demo_T").delete()
    APIKey.objects.filter(user__userid__startswith="demo_T").delete()
    Tourist.objects.filter(userid__startswith="demo_T").delete()

    created = []
    now = timezone.now()

    for i in range(1, 11):  # 10 users: demo_T001 .. demo_T010
        userid = f"demo_T{i:03d}"
        name = random.choice(FIRST_NAMES) + " " + random.choice(FIRST_NAMES)
        email = f"{userid.lower()}@example.com"
        mobile = _random_mobile()
        gender = random.choice(GENDERS)
        dob = _random_dob(min_age=20, max_age=55)
        blood_group = random.choice(BLOOD_GROUPS)
        aadhaar = _random_aadhaar()
        passport = _random_passport()
        emergency_contact = _random_mobile()
        is_mobile_verified = random.choice([True, False])
        email_verified = random.choice([True, False])
        aadhaar_verified = random.choice([True, False])

        tourist = Tourist.objects.create(
            userid=userid,
            name=name,
            email=email,
            gender=gender,
            dob=dob,
            blood_group=blood_group,
            mobile_no=mobile,
            is_mobile_verified=is_mobile_verified,
            email_verified=email_verified,
            aadhaar_no=aadhaar,
            aadhaar_verified=aadhaar_verified,
            passport_no=passport,
            emergency_contact=emergency_contact,
            # created_at auto-set
        )

        # API Key
        api_key_val = secrets.token_hex(20)
        # handle APIKey model: it has `user` OneToOneField and `key`
        APIKey.objects.create(user=tourist, key=api_key_val)

        # Audit logs - a couple of entries
        AuditLog.objects.create(user=tourist, action="ACCOUNT_CREATED", details=f"Seeded demo account {userid}")
        if is_mobile_verified:
            AuditLog.objects.create(user=tourist, action="MOBILE_VERIFIED", details=f"Mobile {mobile} auto-verified for demo user")
        if email_verified:
            AuditLog.objects.create(user=tourist, action="EMAIL_VERIFIED", details=f"Email {email} auto-verified for demo user")
        if aadhaar_verified:
            AuditLog.objects.create(user=tourist, action="AADHAAR_VERIFIED", details=f"Aadhaar {aadhaar} marked verified for demo user")

        # Create OTP objects (a mobile OTP and an email OTP) — short-lived
        otp_code_mobile = f"{random.randint(100000, 999999)}"
        otp_mobile = OTP.objects.create(
            tourist=tourist,
            code=otp_code_mobile,
            created_at=now,
            expires_at=now + timedelta(minutes=10),
            is_used=False,
            type="mobile"
        )
        AuditLog.objects.create(user=tourist, action="OTP_SENT", details=f"mobile otp {otp_code_mobile}")

        otp_code_email = f"{random.randint(100000, 999999)}"
        otp_email = OTP.objects.create(
            tourist=tourist,
            code=otp_code_email,
            created_at=now,
            expires_at=now + timedelta(minutes=10),
            is_used=False,
            type="email"
        )
        AuditLog.objects.create(user=tourist, action="OTP_SENT", details=f"email otp {otp_code_email}")

        # Aadhaar OTP (txn_id random)
        txn = secrets.token_urlsafe(12)
        aadhaar_otp = AadhaarOTP.objects.create(
            tourist=tourist,
            txn_id=txn,
            otp_sent_at=now,
            is_verified=aadhaar_verified
        )
        AuditLog.objects.create(user=tourist, action="AADHAAR_OTP_SENT", details=f"txn:{txn}")

        # Itinerary
        start_date = (now - timedelta(days=2)).date()
        end_date = (now + timedelta(days=2)).date()
        itinerary = Itinerary.objects.create(
            tourist=tourist,
            title="Demo Aizawl Visit",
            start_date=start_date,
            end_date=end_date,
            base_location="Aizawl, Mizoram",
        )

        # Create a couple of Trips (small realistic set)
        place_names = list(AIZAWL_PLACES.keys())
        for tnum in range(1, 4):
            start_name, end_name = random.sample(place_names, 2)
            st_coords = AIZAWL_PLACES[start_name]
            en_coords = AIZAWL_PLACES[end_name]
            start_time = now - timedelta(hours=tnum * 6)
            end_time = start_time + timedelta(hours=1 + random.randint(0, 2))
            Trip.objects.create(
                itinerary=itinerary,
                trip_title=f"Trip {tnum}: {start_name} → {end_name}",
                start_location=start_name,
                end_location=end_name,
                start_time=start_time,
                end_time=end_time,
            )

        # Create 30 recent location pings spaced by 5 minutes ending at "now"
        pings = 30
        earliest = now - timedelta(minutes=5 * (pings - 1))
        timestamp = earliest

        # pick a local base place to jitter around so user appears in one area
        base_place = random.choice(place_names)
        base_lat, base_lon = AIZAWL_PLACES[base_place]

        for j in range(pings):
            jlat, jlon = _jitter(base_lat, base_lon, scale=0.0009)
            TouristLocation.objects.create(
                tourist=tourist,
                latitude=round(jlat, 6),
                longitude=round(jlon, 6),
                timestamp=timestamp,
            )
            timestamp += timedelta(minutes=5)

        created.append({
            "userid": userid,
            "email": email,
            "mobile": mobile,
            "dob": str(dob),
            "aadhaar": aadhaar,
            "passport": passport,
            "api_key": api_key_val[:8] + "..."  # partial for readability
        })

    return JsonResponse({
        "status": "ok",
        "message": "Seeded 10 demo tourists with full details (Aadhaar, dob, passport, OTPs, API keys, location pings).",
        "count": len(created),
        "created": created,
    })






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


