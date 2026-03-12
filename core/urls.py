from django.urls import path
from . import views
from surveyfill.controller import survey_fill_controller
from core.controllers import similarity_controller

urlpatterns = [
    path("auth/register", views.register),
    path("auth/send-register-code", views.send_register_code),
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
    # Internal similarity/vector endpoints
    path(
        "internal/similarity/compute", similarity_controller.compute_user_survey_cosine
    ),
    path("internal/vector/encode", similarity_controller.encode_text_to_vector),
    path(
        "internal/vector/generate-string",
        similarity_controller.generate_placeholder_string,
    ),
    path("internal/vector/generate", similarity_controller.generate_and_store_vector),
    path("internal/similarity/dismiss", similarity_controller.dismiss_survey),
    path("internal/similarity/abandon", similarity_controller.abandon_by_survey),
    path(
        "internal/similarity/abandon/<str:fill_id>", similarity_controller.abandon_fill
    ),
]
