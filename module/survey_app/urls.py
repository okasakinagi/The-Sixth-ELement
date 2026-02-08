from django.urls import path, include
from core import views

urlpatterns = [
    path("", views.index),
    path("api/v1/", include("core.urls")),
    path("api/v1/", include("personal_homepage.urls")),
    path("api/v1/", include("survey_management.urls")),
    path("api/v1/", include("task_hall.urls")),
    path("api/v1/points/", include("points_record.urls")),
    path("api/v1/profile/", include("user_profile_extractor.urls")),
]
