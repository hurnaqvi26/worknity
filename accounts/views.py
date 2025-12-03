from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from accounts.utils import role_required
from .models import EmployeeProfile
from .forms import EmployeeCreateForm

from .forms import SignupForm

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from accounts.models import EmployeeProfile

@login_required
def profile_view(request):
    profile, _ = EmployeeProfile.objects.get_or_create(user=request.user)
    return render(request, "accounts/profile.html", {"profile": profile})

# Signup
def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():

            # Create the user account
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
            )

            # Create EmployeeProfile with default role = EMPLOYEE
            from .models import EmployeeProfile
            EmployeeProfile.objects.create(user=user, role="EMPLOYEE")

            messages.success(request, "Your account has been created. Please login.")
            return redirect("login")
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})


# Login
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


# Logout
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")



@role_required(["ADMIN"])
def create_employee_view(request):
    if request.method == "POST":
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            # Create Django user
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
            )
            # Create employee profile
            EmployeeProfile.objects.create(
                user=user,
                role=form.cleaned_data["role"]
            )
            messages.success(request, "Employee created successfully.")
            return redirect("dashboard")
    else:
        form = EmployeeCreateForm()

    return render(request, "accounts/create_employee.html", {
        "form": form
    })
