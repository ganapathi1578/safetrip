from django.urls import path
from . import views

urlpatterns = [
    path("seed/", views.seed_aizawl_demo, name="seed_aizawl"),

    path("request-otp/", views.request_otp, name="request_otp"), # Moblie
    path("verify-otp/", views.verify_otp, name="verify_otp"),

    path("send-aadhaar-otp/", views.send_aadhaar_otp, name="send_aadhaar_otp"),  # Aadhaar
    path("verify-aadhaar-otp/", views.verify_aadhaar_otp, name="verify_aadhaar_otp"),

    path("request-email-otp/", views.request_email_otp, name="request_email_otp"),  ## Email
    path("verify-email-otp/", views.verify_email_otp, name="verify_email_otp"),

    path('get-tourist-details/', views.get_tourist_details, name='get_tourist_details'),
    path('save-tourist-details/', views.save_tourist_details, name='save_tourist_details'),

    path("save-tourist-location/", views.save_tourist_location, name="save_tourist_location"),
    path("tourist/<str:userid>/", views.get_tourist_details, name="tourist_details"),

     
]