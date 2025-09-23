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
# ModelForm for Zone
# -------------------------
class ZoneForm(forms.ModelForm):
    class Meta:
        model = Zone
        fields = ["name", "latitude", "longitude", "radius"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Zone name"}),
            "latitude": forms.NumberInput(attrs={"step": "0.000001", "placeholder": "Latitude"}),
            "longitude": forms.NumberInput(attrs={"step": "0.000001", "placeholder": "Longitude"}),
            "radius": forms.NumberInput(attrs={"step": "0.1", "placeholder": "Radius"}),
        }
        labels = {field: "" for field in fields}  # cleaner way to remove all labels


# -------------------------
# Plain forms for the nested add_zone page
# -------------------------
class ZoneTypeForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "Type name (e.g., Crime)"})
    )
    description = forms.CharField(
        required=False,
        label="",
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "Description (optional)"})
    )
    DELETE = forms.BooleanField(required=False, label="")  # optional checkbox without label


class ZoneAlertForm(forms.Form):
    start_time = forms.TimeField(
        label="",
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time", "placeholder": "Start Time"})
    )
    end_time = forms.TimeField(
        label="",
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time", "placeholder": "End Time"})
    )
    risk_points = forms.IntegerField(
        label="",
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={"placeholder": "Risk Points"})
    )
    type_index = forms.IntegerField(widget=forms.HiddenInput())
    DELETE = forms.BooleanField(required=False, label="")


from django.forms import formset_factory
ZoneTypeFormSet = formset_factory(ZoneTypeForm, extra=1, can_delete=True)
ZoneAlertFormSet = formset_factory(ZoneAlertForm, extra=0, can_delete=True)