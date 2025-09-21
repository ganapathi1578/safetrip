from django.urls import path
from . import views

urlpatterns = [
    #path("seed/", views.seed_aizawl_view, name="seed_aizawl"),

    path("request-otp/", views.request_otp, name="request_otp"), # Moblie
    path("verify-otp/", views.verify_otp, name="verify_otp"),

    path("send-aadhaar-otp/", views.send_aadhaar_otp, name="send_aadhaar_otp"),  # Aadhaar
    path("verify-aadhaar-otp/", views.verify_aadhaar_otp, name="verify_aadhaar_otp"),

    path("request-email-otp/", views.request_email_otp, name="request_email_otp"),  ## Email
    path("verify-email-otp/", views.verify_email_otp, name="verify_email_otp"),
]
