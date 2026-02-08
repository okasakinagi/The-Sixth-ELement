from django.urls import path
from user_profile_extractor.controller.profile_extractor_controller import get_user_profile_summary

urlpatterns = [
    path("summary", get_user_profile_summary, name="user_profile_summary"),
]
