from django.db.models import Count, Q

from core.models import PointsLog, Questionnaire, Response, Survey


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
        return survey

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
