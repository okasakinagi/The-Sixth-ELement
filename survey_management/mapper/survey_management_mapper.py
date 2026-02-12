from django.db.models import Count, Q

from core.models import PointsLog, Question, QuestionOption, Questionnaire, Response, Survey


class SurveyManagementMapper:
    @staticmethod
    def list_surveys(owner, status_list=None, keyword=None):
        queryset = Survey.objects.filter(owner=owner)
        if status_list:
            queryset = queryset.filter(status__in=status_list)
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) | Q(description__icontains=keyword)
            )
        return list(queryset.order_by("-updated_at", "-id"))

    @staticmethod
    def get_survey(survey_id):
        return Survey.objects.select_related("owner", "active_questionnaire").filter(
            id=survey_id
        ).first()

    @staticmethod
    def get_owner_survey(owner, survey_id):
        return Survey.objects.select_related("owner", "active_questionnaire").filter(
            id=survey_id, owner=owner
        ).first()

    @staticmethod
    def get_completed_counts(survey_ids):
        if not survey_ids:
            return {}
        rows = (
            Response.objects.filter(
                survey_id__in=survey_ids, submitted_at__isnull=False
            )
            .values("survey_id")
            .annotate(cnt=Count("id"))
        )
        return {row["survey_id"]: row["cnt"] for row in rows}

    @staticmethod
    def delete_survey(survey):
        survey.delete()

    @staticmethod
    def create_survey(owner, data):
        survey = Survey.objects.create(**data)
        questionnaire = Questionnaire.objects.create(
            survey=survey,
            version=1,
            status="published",
            title=survey.title,
        )
        survey.active_questionnaire = questionnaire
        survey.save(update_fields=["active_questionnaire"])
        try:
            # ensure survey vector is generated at creation time
            from core.services.similarity_service import SimilarityService

            SimilarityService.generate_and_store_vector("survey", str(survey.id))
        except Exception:
            # non-fatal: vector generation failure shouldn't block creation
            pass
        return survey

    @staticmethod
    def create_draft_survey(owner, title, subtitle=None):
        survey = Survey.objects.create(
            owner=owner,
            title=title,
            description=subtitle,
            status="draft",
            reward_points=0,
            publish_cost_points=0,
        )
        questionnaire = Questionnaire.objects.create(
            survey=survey,
            version=1,
            status="draft",
            title=title,
        )
        survey.active_questionnaire = questionnaire
        survey.save(update_fields=["active_questionnaire"])
        try:
            from core.services.similarity_service import SimilarityService

            SimilarityService.generate_and_store_vector("survey", str(survey.id))
        except Exception:
            pass
        return survey

    @staticmethod
    def get_questions(questionnaire_id):
        return list(
            Question.objects.filter(questionnaire_id=questionnaire_id).order_by(
                "order_no", "id"
            )
        )

    @staticmethod
    def delete_questions(questionnaire_id):
        Question.objects.filter(questionnaire_id=questionnaire_id).delete()

    @staticmethod
    def delete_question(questionnaire_id, question_id):
        return Question.objects.filter(
            questionnaire_id=questionnaire_id,
            id=question_id,
        ).delete()

    @staticmethod
    def create_question(questionnaire, payload):
        question = Question.objects.create(
            questionnaire=questionnaire,
            order_no=payload["order_no"],
            type=payload["type"],
            title=payload["title"],
            is_required=payload.get("required", True),
            config_json=payload.get("config_json"),
        )
        options = payload.get("options") or []
        option_rows = []
        for idx, label in enumerate(options, start=1):
            option_rows.append(
                QuestionOption(
                    question=question,
                    order_no=idx,
                    label=label,
                    value=str(label),
                )
            )
        if option_rows:
            QuestionOption.objects.bulk_create(option_rows)
        return question

    @staticmethod
    def create_points_log(user, delta, reason, ref_type=None, ref_id=None):
        return PointsLog.objects.create(
            user=user,
            points_type="publish_cost" if delta < 0 else "reward",
            delta=delta,
            reason=reason,
            ref_type=ref_type,
            ref_id=ref_id,
        )
