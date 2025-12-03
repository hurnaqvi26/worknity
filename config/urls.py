from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # App-level URL includes
    path("", include("accounts.urls")),
    path("", include("tasks.urls")),
    path("", include("comments.urls")),
]
