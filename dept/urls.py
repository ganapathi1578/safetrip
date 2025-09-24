from django.urls import path
from . import views


urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.home_view, name='home'),
    path("zones/", views.add_zone, name="add_zone"),
    path("zones_json/", views.zones_json, name="zones_json"),
    path("zone_detail/<int:zone_id>/", views.zone_detail_json, name="zone_detail_json"),
    path("map/", views.safetour_map, name="safetour_map"),
    path("api/filter_options/", views.api_filter_options, name="api_filter_options"),
    path("api/alerts/", views.api_alerts, name="api_alerts"),
    path("api/tourists/latest/", views.api_tourists_latest, name="api_tourists_latest"),
    path("tourist/<str:userid>/details/", views.get_tourist_details, name="tourist_details"),
]