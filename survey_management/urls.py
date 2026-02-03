from django.urls import path

from survey_management.controller import survey_management_controller


urlpatterns = [
    path("surveys", survey_management_controller.surveys_handler),
    path("surveys/summary", survey_management_controller.surveys_summary),
    path("surveys/<str:survey_id>", survey_management_controller.survey_detail_handler),
    path("surveys/<str:survey_id>/pause", survey_management_controller.pause_survey),
    path("surveys/<str:survey_id>/resume", survey_management_controller.resume_survey),
    path("surveys/<str:survey_id>/publish", survey_management_controller.publish_survey),
]
