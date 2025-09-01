from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import PoliceOfficer

class PoliceOfficerRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = PoliceOfficer
        fields = ["police_id", "name", "email", "mobile_no", "rank", "station", "password"]

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

class PoliceOfficerLoginForm(forms.Form):
    police_id = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput)

