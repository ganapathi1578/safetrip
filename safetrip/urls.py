from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

def home(request):
    return render(request, "base.html")  # temporary home page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("dept.urls")),
    path('tour/', include("tourist.urls")),
]