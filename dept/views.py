from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import PoliceOfficerRegistrationForm, PoliceOfficerLoginForm
from .models import PoliceOfficer

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