from django.urls import path
from .views import signup_view, login_view, logout_view, create_employee_view, profile_view

urlpatterns = [
    path("", login_view, name="home"),  # FIXED ROOT URL
    path("signup/", signup_view, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile_view"),
    path("employees/create/", create_employee_view, name="create_employee"),
]
