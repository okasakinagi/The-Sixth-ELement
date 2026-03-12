import json
import os
import re
from pathlib import Path
from datetime import timezone as dt_timezone
from urllib import error as url_error
from urllib import request as url_request
from django.utils import timezone

from core.models import Questionnaire
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

    def create_draft(self, user, data):
        title = (data.get("title") or "").strip()
        if not title:
            raise SurveyManagementError(422, "title required")
        subtitle = data.get("subtitle")
        survey = self.mapper.create_draft_survey(user, title, subtitle=subtitle)
        return {
            "id": self._public_survey_id(survey.id),
            "title": survey.title,
            "status": "draft",
        }

    def get_draft(self, user, survey_id):
        survey, questionnaire = self._get_draft_or_error(user, survey_id)
        questions = self.mapper.get_questions(questionnaire.id)
        return {
            "id": self._public_survey_id(survey.id),
            "title": survey.title,
            "subtitle": survey.description or "",
            "status": "draft",
            "questions": [self._question_payload(q) for q in questions],
            "updated_at": self._iso_str(survey.updated_at),
        }

    def update_draft(self, user, survey_id, data):
        survey, questionnaire = self._get_draft_or_error(user, survey_id)
        title = data.get("title")
        subtitle = data.get("subtitle")
        updated_fields = []
        if title is not None:
            title = str(title).strip()
            if not title:
                raise SurveyManagementError(422, "title required")
            survey.title = title
            updated_fields.append("title")
        if subtitle is not None:
            survey.description = subtitle
            updated_fields.append("description")

        questions = data.get("questions")
        if questions is not None:
            normalized = self._normalize_questions_payload(questions)
            self.mapper.delete_questions(questionnaire.id)
            for payload in normalized:
                self.mapper.create_question(questionnaire, payload)
            updated_fields.append("updated_at")

        if updated_fields:
            updated_fields.append("updated_at")
            survey.save(update_fields=list(set(updated_fields)))
        return {
            "id": self._public_survey_id(survey.id),
            "updated_at": self._iso_str(survey.updated_at),
        }

    def delete_draft_question(self, user, survey_id, question_id):
        _, questionnaire = self._get_draft_or_error(user, survey_id)
        deleted, _ = self.mapper.delete_question(questionnaire.id, question_id)
        if deleted == 0:
            raise SurveyManagementError(404, "question not found")
        return {"success": True}

    def ai_generate_questions(self, user, survey_id, data):
        survey, questionnaire = self._get_draft_or_error(user, survey_id)
        prompt = (data.get("prompt") or "").strip()
        if not prompt:
            raise SurveyManagementError(422, "prompt required")
        question_count = data.get("question_count", 10)
        try:
            question_count = int(question_count)
        except (TypeError, ValueError):
            raise SurveyManagementError(422, "question_count must be a number")
        if question_count <= 0:
            raise SurveyManagementError(422, "question_count must be >= 1")

        questions = self._call_siliconflow(prompt, question_count)
        normalized = self._normalize_questions_payload(questions, default_is_ai=True)
        self.mapper.delete_questions(questionnaire.id)
        for payload in normalized:
            self.mapper.create_question(questionnaire, payload)

        survey.updated_at = timezone.now()
        survey.save(update_fields=["updated_at"])
        return {
            "draft_id": self._public_survey_id(survey.id),
            "questions": [self._question_payload(q) for q in self.mapper.get_questions(questionnaire.id)],
        }

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

    def _public_qid(self, question_id):
        return f"q_{question_id}"

    def _date_str(self, dt):
        if not dt:
            return None
        return dt.date().isoformat()

    def _iso_str(self, dt):
        if not dt:
            return None
        return dt.astimezone(dt_timezone.utc).isoformat().replace("+00:00", "Z")

    def _get_draft_or_error(self, user, survey_id):
        survey = self.mapper.get_owner_survey(user, survey_id)
        if not survey:
            raise SurveyManagementError(404, "survey not found")
        if survey.status != "draft":
            raise SurveyManagementError(409, "survey is not a draft")
        questionnaire = survey.active_questionnaire
        if not questionnaire:
            questionnaire = Questionnaire.objects.create(
                survey=survey,
                version=1,
                status="draft",
                title=survey.title,
            )
            survey.active_questionnaire = questionnaire
            survey.save(update_fields=["active_questionnaire"])
        return survey, questionnaire

    def _question_payload(self, question):
        options = [
            opt.label
            for opt in question.questionoption_set.all().order_by("order_no", "id")
        ]
        config = question.config_json or {}
        return {
            "id": self._public_qid(question.id),
            "type": question.type,
            "title": question.title,
            "options": options,
            "required": question.is_required,
            "order": question.order_no,
            "is_ai": bool(config.get("is_ai")) if isinstance(config, dict) else False,
        }

    def _normalize_questions_payload(self, questions, default_is_ai=False):
        if not isinstance(questions, list):
            raise SurveyManagementError(422, "questions must be a list")
        normalized = []
        allowed_types = {"single", "multi", "text", "multi-text"}
        for idx, item in enumerate(questions, start=1):
            if not isinstance(item, dict):
                raise SurveyManagementError(422, "invalid questions payload")
            qtype = (item.get("type") or "").strip().lower()
            if qtype not in allowed_types:
                raise SurveyManagementError(422, "invalid question type")
            title = (item.get("title") or "").strip()
            if not title:
                raise SurveyManagementError(422, "question title required")
            options = item.get("options") or []
            if qtype in {"single", "multi"}:
                if not isinstance(options, list) or not options:
                    raise SurveyManagementError(422, "options required")
                cleaned = []
                for opt in options:
                    opt_str = str(opt).strip()
                    if not opt_str:
                        continue
                    cleaned.append(opt_str)
                if not cleaned:
                    raise SurveyManagementError(422, "options required")
                options = cleaned
            else:
                if options and not isinstance(options, list):
                    raise SurveyManagementError(422, "options must be a list")

            required = item.get("required")
            if required is None:
                required = True
            is_ai = item.get("is_ai", default_is_ai)
            order_no = item.get("order") or idx
            try:
                order_no = int(order_no)
            except (TypeError, ValueError):
                order_no = idx
            normalized.append(
                {
                    "order_no": order_no,
                    "type": qtype,
                    "title": title,
                    "options": options,
                    "required": bool(required),
                    "config_json": {"is_ai": bool(is_ai)},
                }
            )
        return normalized

    def _call_siliconflow(self, prompt, question_count):
        config = self._load_ai_config()
        api_key = config.get("api_key") or os.environ.get("SILICONFLOW_API_KEY")
        if not api_key:
            raise SurveyManagementError(500, "SILICONFLOW_API_KEY not configured")
        base_url = config.get("base_url") or os.environ.get(
            "SILICONFLOW_BASE_URL",
            "https://api.siliconflow.cn/v1/chat/completions",
        )
        normalized_base = base_url.rstrip("/")
        if normalized_base.endswith("/v1"):
            base_url = f"{normalized_base}/chat/completions"
        elif "chat/completions" not in normalized_base:
            base_url = normalized_base
        model = config.get("model") or os.environ.get("SILICONFLOW_MODEL")
        if not model:
            raise SurveyManagementError(500, "SILICONFLOW_MODEL not configured")

        instruction = (
            "You are a survey designer. Return JSON only. "
            "Output format: {\"questions\":[{\"type\":\"single|multi|text|multi-text\","
            "\"title\":\"...\",\"options\":[...],\"required\":true}]}. "
            f"Generate {question_count} questions."
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        }
        req = url_request.Request(
            base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with url_request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
        except url_error.HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else str(exc)
            raise SurveyManagementError(502, f"llm error: {error_body}")
        except url_error.URLError as exc:
            raise SurveyManagementError(502, f"llm error: {str(exc)}")

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise SurveyManagementError(502, "llm returned invalid response")

        text = None
        if isinstance(data, dict):
            choices = data.get("choices") or []
            if choices:
                first = choices[0] or {}
                message = first.get("message") or {}
                text = message.get("content") or first.get("text")
        if not text:
            raise SurveyManagementError(502, "llm returned empty output")

        json_text = self._extract_json(text)
        try:
            payload = json.loads(json_text)
        except json.JSONDecodeError:
            raise SurveyManagementError(502, "llm returned non-json output")

        if isinstance(payload, dict):
            questions = payload.get("questions")
        elif isinstance(payload, list):
            questions = payload
        else:
            questions = None
        if questions is None:
            raise SurveyManagementError(502, "llm output missing questions")
        return questions

    def _load_ai_config(self):
        project_root = Path(__file__).resolve().parents[2]
        config_path = project_root / "deploy" / "ai_config.json"
        if not config_path.exists():
            return {}
        try:
            content = config_path.read_text(encoding="utf-8")
            data = json.loads(content)
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {
            "api_key": str(data.get("api_key") or "").strip(),
            "model": str(data.get("model") or "").strip(),
            "base_url": str(data.get("base_url") or "").strip(),
        }

    def _extract_json(self, text):
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return match.group(0)
        match = re.search(r"\[[\s\S]*\]", text)
        if match:
            return match.group(0)
        return text
