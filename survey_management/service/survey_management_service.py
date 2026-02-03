from datetime import timezone as dt_timezone
from django.utils import timezone

from survey_management.mapper.survey_management_mapper import SurveyManagementMapper


class SurveyManagementError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


class SurveyManagementService:
    STATUS_LIVE_INTERNAL = {"published", "active", "live"}
    STATUS_ENDED_INTERNAL = {"ended", "closed", "expired", "rejected"}

    API_STATUS_TO_INTERNAL = {
        "draft": ["draft"],
        "live": ["published", "active", "live"],
        "paused": ["paused"],
        "ended": ["ended", "closed", "expired", "rejected"],
    }

    def __init__(self):
        self.mapper = SurveyManagementMapper()

    def list_surveys(self, user, filters):
        keyword = (filters.get("keyword") or "").strip()
        status = (filters.get("status") or "").strip()
        status_list = None
        if status:
            status_list = self.API_STATUS_TO_INTERNAL.get(status)
            if not status_list:
                raise SurveyManagementError(422, "invalid status")

        surveys = self.mapper.list_surveys(user, status_list=status_list, keyword=keyword)
        completed_counts = self.mapper.get_completed_counts([survey.id for survey in surveys])

        items = []
        for survey in surveys:
            completed = completed_counts.get(survey.id, survey.completed or 0)
            items.append(self._survey_list_payload(survey, completed))
        return {"items": items}

    def get_summary(self, user):
        surveys = self.mapper.list_surveys(user)
        completed_counts = self.mapper.get_completed_counts([survey.id for survey in surveys])
        summary = {"draft_count": 0, "live_count": 0, "ended_count": 0}
        for survey in surveys:
            completed = completed_counts.get(survey.id, survey.completed or 0)
            status = self._to_api_status(survey.status, completed, survey.target or 0)
            if status == "draft":
                summary["draft_count"] += 1
            elif status == "ended":
                summary["ended_count"] += 1
            else:
                summary["live_count"] += 1
        return summary

    def get_detail(self, user, survey_id):
        survey = self.mapper.get_survey(survey_id)
        if not survey:
            raise SurveyManagementError(404, "survey not found")
        completed_counts = self.mapper.get_completed_counts([survey.id])
        completed = completed_counts.get(survey.id, survey.completed or 0)
        return self._survey_detail_payload(survey, completed)

    def delete_survey(self, user, survey_id):
        survey = self.mapper.get_owner_survey(user, survey_id)
        if not survey:
            raise SurveyManagementError(404, "survey not found")
        self.mapper.delete_survey(survey)
        return {"success": True}

    def pause_survey(self, user, survey_id):
        survey = self.mapper.get_owner_survey(user, survey_id)
        if not survey:
            raise SurveyManagementError(404, "survey not found")
        if survey.status not in self.STATUS_LIVE_INTERNAL:
            raise SurveyManagementError(409, "survey cannot be paused")
        survey.status = "paused"
        survey.save(update_fields=["status"])
        return {"id": self._public_survey_id(survey.id), "status": "paused"}

    def resume_survey(self, user, survey_id):
        survey = self.mapper.get_owner_survey(user, survey_id)
        if not survey:
            raise SurveyManagementError(404, "survey not found")
        if survey.status != "paused":
            raise SurveyManagementError(409, "survey cannot be resumed")
        survey.status = "published"
        survey.save(update_fields=["status"])
        return {"id": self._public_survey_id(survey.id), "status": "live"}

    def publish_survey(self, user, survey_id, data):
        survey = self.mapper.get_owner_survey(user, survey_id)
        if not survey:
            raise SurveyManagementError(404, "survey not found")
        if survey.status != "draft":
            raise SurveyManagementError(409, "survey cannot be published")

        budget_points = data.get("budget_points")
        target = data.get("target")
        try:
            budget_points = int(budget_points)
        except (TypeError, ValueError):
            raise SurveyManagementError(422, "budget_points must be a number")
        try:
            target = int(target)
        except (TypeError, ValueError):
            raise SurveyManagementError(422, "target must be a number")

        if budget_points < 0:
            raise SurveyManagementError(422, "budget_points must be >= 0")
        if target <= 0:
            raise SurveyManagementError(422, "target must be >= 1")

        if user.points < budget_points:
            raise SurveyManagementError(422, "not enough points to publish survey")

        if not survey.reward_points and budget_points > 0:
            survey.reward_points = max(1, budget_points // target) if target else 0

        survey.target = target
        survey.publish_cost_points = budget_points
        survey.status = "published"
        survey.updated_at = timezone.now()
        survey.save(update_fields=["target", "publish_cost_points", "reward_points", "status", "updated_at"])

        if budget_points > 0:
            user.points -= budget_points
            user.save(update_fields=["points"])
            self.mapper.create_points_log(
                user=user,
                delta=-budget_points,
                reason="发布问卷消耗",
                ref_type="survey",
                ref_id=survey.id,
            )

        return {
            "id": self._public_survey_id(survey.id),
            "status": "live",
            "published_at": timezone.now().astimezone(dt_timezone.utc).isoformat().replace("+00:00", "Z"),
        }

    def create_survey(self, user, data):
        title = (data.get("title") or "").strip()
        if not title:
            raise SurveyManagementError(422, "title required")

        reward_points = data.get("reward_points", 0) or 0
        try:
            reward_points = int(reward_points)
        except (TypeError, ValueError):
            raise SurveyManagementError(422, "reward_points must be a number")
        if reward_points < 0:
            raise SurveyManagementError(422, "reward_points must be >= 0")
        if user.points < reward_points:
            raise SurveyManagementError(422, "not enough points to publish survey")

        estimated_minutes = data.get("estimated_minutes")
        if estimated_minutes is not None and estimated_minutes != "":
            try:
                estimated_minutes = int(estimated_minutes)
            except (TypeError, ValueError):
                raise SurveyManagementError(422, "estimated_minutes must be a number")
        else:
            estimated_minutes = None

        survey = self.mapper.create_survey(
            owner=user,
            data={
                "owner": user,
                "title": title,
                "description": data.get("description"),
                "reward_points": reward_points,
                "publish_cost_points": reward_points,
                "deadline": data.get("deadline"),
                "estimated_minutes": estimated_minutes,
                "status": "published",
            },
        )
        if reward_points > 0:
            user.points -= reward_points
            user.save(update_fields=["points"])
            self.mapper.create_points_log(
                user=user,
                delta=-reward_points,
                reason="发布问卷消耗",
                ref_type="survey",
                ref_id=survey.id,
            )
        return {"id": self._public_survey_id(survey.id), "status": "active"}

    def _survey_list_payload(self, survey, completed):
        target = survey.target or 0
        return {
            "id": self._public_survey_id(survey.id),
            "title": survey.title,
            "subtitle": survey.description or "",
            "status": self._to_api_status(survey.status, completed, target),
            "completed": completed,
            "target": target,
            "updated_at": self._date_str(survey.updated_at),
            "created_at": self._iso_str(survey.created_at),
        }

    def _survey_detail_payload(self, survey, completed):
        target = survey.target or 0
        return {
            "id": self._public_survey_id(survey.id),
            "title": survey.title,
            "subtitle": survey.description or "",
            "description": survey.description or "",
            "link": None,
            "reward_points": survey.reward_points,
            "estimated_minutes": survey.estimated_minutes,
            "deadline": self._iso_str(survey.deadline) if survey.deadline else None,
            "status": self._to_api_status(survey.status, completed, target),
            "created_at": self._iso_str(survey.created_at),
            "updated_at": self._date_str(survey.updated_at),
            "owner_id": self._public_user_id(survey.owner_id),
            "completed": completed,
            "target": target,
        }

    def _to_api_status(self, internal_status, completed, target):
        if target and completed >= target:
            return "ended"
        if internal_status in self.STATUS_LIVE_INTERNAL:
            return "live"
        if internal_status == "paused":
            return "paused"
        if internal_status in self.STATUS_ENDED_INTERNAL:
            return "ended"
        return "draft"

    def _public_survey_id(self, survey_id):
        return f"s_{survey_id}"

    def _public_user_id(self, user_id):
        return f"u_{user_id}"

    def _date_str(self, dt):
        if not dt:
            return None
        return dt.date().isoformat()

    def _iso_str(self, dt):
        if not dt:
            return None
        return dt.astimezone(dt_timezone.utc).isoformat().replace("+00:00", "Z")
