from django.urls import path
from . import views
from surveyfill.controller import survey_fill_controller

urlpatterns = [
    path("auth/register", views.register),
    path("auth/login", views.login),
    path("auth/send-reset-code", views.send_reset_code),
    path("auth/reset-password", views.verify_reset_code),
    path("users/me", views.user_me),
    # Survey management routes are served by survey_management.urls
    path("surveys/<str:survey_id>/close", views.close_survey),
    path("surveys/<str:survey_id>/fill", survey_fill_controller.survey_fill_detail),
    path("surveys/<str:survey_id>/fills", survey_fill_controller.submit_survey_fill),
    path("fills/<str:fill_id>/review", views.review_fill),
    path("fills/me", views.my_fills),
    path("points/logs", views.points_logs),
    path("reports", views.create_report),
]
