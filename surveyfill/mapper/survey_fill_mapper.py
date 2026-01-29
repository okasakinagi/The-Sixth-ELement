"""
SurveyFill Mapper - 数据访问层
负责问卷填写相关的数据查询与写入
"""

from django.db import transaction
from django.db.models import Prefetch

from core.models import Answer, Question, QuestionOption, Questionnaire, Response, Survey


class SurveyFillMapper:
    @staticmethod
    def get_survey(survey_id):
        return (
            Survey.objects.select_related("active_questionnaire", "owner")
            .filter(id=survey_id)
            .first()
        )

    @staticmethod
    def get_questionnaire(questionnaire_id):
        return Questionnaire.objects.filter(id=questionnaire_id).first()

    @staticmethod
    def get_questions(questionnaire_id):
        return (
            Question.objects.filter(questionnaire_id=questionnaire_id)
            .order_by("order_no", "id")
            .prefetch_related(
                Prefetch(
                    "questionoption_set",
                    queryset=QuestionOption.objects.order_by("order_no", "id"),
                )
            )
        )

    @staticmethod
    def response_exists(survey_id, user_id):
        return Response.objects.filter(survey_id=survey_id, user_id=user_id).exists()

    @staticmethod
    def create_response_with_answers(
        survey, questionnaire, user, duration_seconds, answers
    ):
        """
        创建答卷并写入答案

        Args:
            survey: Survey实例
            questionnaire: Questionnaire实例
            user: AppUser实例
            duration_seconds: int
            answers: list[dict] with keys: question_id, value_text, value_json
        """
        with transaction.atomic():
            response = Response.objects.create(
                survey=survey,
                questionnaire=questionnaire,
                user=user,
                status="submitted",
                submitted_at=None,
                duration_seconds=duration_seconds,
            )
            if answers:
                Answer.objects.bulk_create(
                    [
                        Answer(
                            response=response,
                            question_id=item["question_id"],
                            value_text=item.get("value_text"),
                            value_json=item.get("value_json"),
                        )
                        for item in answers
                    ]
                )
            return response
