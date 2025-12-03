from django.urls import path
from .views import dashboard_view, task_create_view, task_edit_view, task_delete_view

urlpatterns = [
    path("dashboard/", dashboard_view, name="dashboard"),
    path("tasks/create/", task_create_view, name="task_create"),
    path("tasks/<str:task_id>/edit/", task_edit_view, name="task_edit"),
    path("tasks/<str:task_id>/delete/", task_delete_view, name="task_delete"),
]
