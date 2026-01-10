from django.urls import path, include
from core import views

urlpatterns = [
    path("", views.index),
    path("api/v1/", include("core.urls")),
]
