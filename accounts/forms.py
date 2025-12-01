from django import forms
from django.contrib.auth.models import User

from .models import EmployeeProfile  # <-- important import


# Signup form for creating a new user account
class SignupForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]

    # Validate matching passwords
    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")

        if p1 != p2:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


# Form for Admin to create employees with a specific role
class EmployeeCreateForm(forms.Form):
    username = forms.CharField(label="Username")
    email = forms.EmailField(label="Email", required=False)
    first_name = forms.CharField(label="First name", required=False)
    last_name = forms.CharField(label="Last name", required=False)
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Password"
    )

    # Here we use the ROLE_CHOICES from EmployeeProfile model
    role = forms.ChoiceField(
        choices=EmployeeProfile.ROLE_CHOICES,
        label="Role"
    )
