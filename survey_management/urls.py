from django.urls import path

from survey_management.controller import survey_management_controller


urlpatterns = [
    path("surveys", survey_management_controller.surveys_handler),
    path("surveys/drafts", survey_management_controller.survey_drafts_handler),
    path(
        "surveys/drafts/<str:draft_id>",
        survey_management_controller.survey_draft_detail,
    ),
    path(
        "surveys/drafts/<str:draft_id>/ai-generate",
        survey_management_controller.survey_draft_ai_generate,
    ),
    path(
        "surveys/drafts/<str:draft_id>/questions/<str:question_id>",
        survey_management_controller.survey_draft_delete_question,
    ),
    path("surveys/summary", survey_management_controller.surveys_summary),
    path("surveys/<str:survey_id>", survey_management_controller.survey_detail_handler),
    path("surveys/<str:survey_id>/pause", survey_management_controller.pause_survey),
    path("surveys/<str:survey_id>/resume", survey_management_controller.resume_survey),
    path(
        "surveys/<str:survey_id>/publish", survey_management_controller.publish_survey
    ),
    path(
        "surveys/<str:survey_id>/cancel", survey_management_controller.cancel_publish
    ),
    path(
        "surveys/<str:survey_id>/evaluate",
        survey_management_controller.survey_evaluate_handler,
    ),
]
