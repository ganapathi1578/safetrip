# dept/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import PoliceOfficer, Zone, ZoneType, ZoneAlert

# -------------------------
# PoliceOfficer forms (if you still use these)
# -------------------------
class PoliceOfficerRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    class Meta:
        model = PoliceOfficer
        fields = ["police_id", "name", "email", "mobile_no", "rank", "station", "password"]

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        pw2 = cleaned.get("confirm_password")
        if pw and pw2 and pw != pw2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

class PoliceOfficerLoginForm(forms.Form):
    police_id = forms.CharField(max_length=50, label=_("Police ID"))
    password = forms.CharField(widget=forms.PasswordInput, label=_("Password"))


# -------------------------
# ModelForm for Zone (useful for admin or edit existing zone)
# -------------------------
class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ["name", "latitude", "longitude", "radius"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Zone name"}),
            "latitude": forms.NumberInput(attrs={"step": "0.000001"}),
            "longitude": forms.NumberInput(attrs={"step": "0.000001"}),
            "radius": forms.NumberInput(attrs={"step": "0.1"}),
        }


# -------------------------
# Plain forms for the nested add_zone page (used with formsets + JS)
# - ZoneTypeForm: user provides name + description for each type (no zone FK)
# - ZoneAlertForm: user provides start/end/risk and a hidden `type_index` linking it to a type
# These are NOT ModelForms because we create model instances in the view and map them.
# -------------------------
class ZoneTypeForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Type name (e.g., Crime)"})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Description (optional)"})
    )
    # Optional delete checkbox for formset behavior
    DELETE = forms.BooleanField(required=False)

class ZoneAlertForm(forms.Form):
    start_time = forms.TimeField(widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}))
    end_time = forms.TimeField(widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}))
    risk_points = forms.IntegerField(min_value=0, max_value=100)
    # hidden integer linking this alert to a ZoneType form index (0-based)
    type_index = forms.IntegerField(widget=forms.HiddenInput())
    DELETE = forms.BooleanField(required=False)


# Convenience factories for views (import these in views.py)
from django.forms import formset_factory
ZoneTypeFormSet = formset_factory(ZoneTypeForm, extra=1, can_delete=True)
ZoneAlertFormSet = formset_factory(ZoneAlertForm, extra=0, can_delete=True)
