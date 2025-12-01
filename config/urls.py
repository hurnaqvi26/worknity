from django.contrib import admin
from django.urls import path

from accounts.views import signup_view, login_view, logout_view
from tasks.views import dashboard_view  # We create this next
from accounts.views import create_employee_view
from tasks.views import task_create_view, task_edit_view, task_delete_view
from comments.views import add_comment_view

urlpatterns = [
    path("admin/", admin.site.urls),

    # Authentication routes
    path("signup/", signup_view, name="signup"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # Default route
    path("", login_view),

    # Dashboard
    path("dashboard/", dashboard_view, name="dashboard"),
    
    path("employees/create/", create_employee_view, name="create_employee"),
    
    path("tasks/create/", task_create_view, name="task_create"),
path("tasks/<str:task_id>/edit/", task_edit_view, name="task_edit"),
path("tasks/<str:task_id>/delete/", task_delete_view, name="task_delete"),
path("tasks/<str:task_id>/comment/", add_comment_view, name="add_comment"),
]
