from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.home_view, name='home'),
    path("zones/add/", views.add_zone, name="add_zone"),
    path("zones_json/", views.zones_json, name="zones_json"),
    path("zone_detail/<int:zone_id>/", views.zone_detail_json, name="zone_detail_json"),
]
