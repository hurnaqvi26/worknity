from django.urls import path
from .views import add_comment_view

urlpatterns = [
    path("tasks/<str:task_id>/comment/", add_comment_view, name="add_comment"),
]
