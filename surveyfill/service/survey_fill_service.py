"""
SurveyFill Service - 业务逻辑层
处理问卷填写的校验、格式转换与提交
"""

import re
from django.utils import timezone

from surveyfill.mapper.survey_fill_mapper import SurveyFillMapper


class SurveyFillError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


class SurveyFillService:
    def __init__(self):
        self.mapper = SurveyFillMapper()

    def get_survey_fill(self, survey_id):
        survey_pk = self._parse_int_id(survey_id)
        if survey_pk is None:
            raise SurveyFillError(422, "invalid survey id")
        survey = self.mapper.get_survey(survey_pk)
        if not survey:
            raise SurveyFillError(404, "survey not found")
        if survey.status != "published":
            raise SurveyFillError(422, "survey not active")
        questionnaire = survey.active_questionnaire
        if not questionnaire or questionnaire.status != "published":
            raise SurveyFillError(422, "survey questionnaire not ready")

        questions = list(self.mapper.get_questions(questionnaire.id))
        question_payloads = [self._question_payload(q) for q in questions]
        return {
            "id": str(survey.id),
            "title": survey.title,
            "subtitle": survey.description or "",
            "questions": question_payloads,
        }

    def submit_survey_fill(self, survey_id, user, data):
        survey_pk = self._parse_int_id(survey_id)
        if survey_pk is None:
            raise SurveyFillError(422, "invalid survey id")
        survey = self.mapper.get_survey(survey_pk)
        if not survey:
            raise SurveyFillError(404, "survey not found")
        if survey.status != "published":
            raise SurveyFillError(422, "survey not active")
        if survey.owner_id == user.id:
            raise SurveyFillError(422, "cannot fill your own survey")
        if self.mapper.response_exists(survey.id, user.id):
            raise SurveyFillError(422, "already filled")

        questionnaire = survey.active_questionnaire
        if not questionnaire or questionnaire.status != "published":
            raise SurveyFillError(422, "survey questionnaire not ready")

        duration_seconds = data.get("duration_seconds")
        if duration_seconds is None:
            raise SurveyFillError(422, "duration_seconds required")
        try:
            duration_seconds = int(duration_seconds)
        except (TypeError, ValueError):
            raise SurveyFillError(422, "duration_seconds must be a number")
        if duration_seconds < 10:
            raise SurveyFillError(422, "fill duration too short")

        answers = data.get("answers")
        if not isinstance(answers, list):
            raise SurveyFillError(422, "answers required")

        questions = list(self.mapper.get_questions(questionnaire.id))
        question_map = {q.id: q for q in questions}
        option_map = self._build_option_map(questions)

        answer_map = {}
        for item in answers:
            if not isinstance(item, dict):
                raise SurveyFillError(422, "invalid answers payload")
            question_id = self._parse_question_id(item.get("question_id"))
            if question_id is None:
                raise SurveyFillError(422, "invalid question id")
            if question_id not in question_map:
                raise SurveyFillError(
                    422, f"question {self._public_qid(question_id)} not found"
                )
            answer_map[question_id] = item.get("value")

        for question in questions:
            qid = question.id
            value = answer_map.get(qid)
            if question.is_required and self._is_empty_answer(value):
                raise SurveyFillError(422, f"question {self._public_qid(qid)} is required")

        answer_payloads = []
        for question in questions:
            qid = question.id
            if qid not in answer_map:
                continue
            value = answer_map[qid]
            if self._is_empty_answer(value):
                continue
            self._validate_answer(question, value, option_map.get(qid) or [])
            value_text, value_json = self._normalize_answer_value(question, value)
            answer_payloads.append(
                {
                    "question_id": qid,
                    "value_text": value_text,
                    "value_json": value_json,
                }
            )

        response = self.mapper.create_response_with_answers(
            survey,
            questionnaire,
            user,
            duration_seconds,
            answer_payloads,
        )
        response.submitted_at = timezone.now()
        response.save(update_fields=["submitted_at"])

        return {
            "id": str(response.id),
            "status": response.status,
            "points_awarded": 0,
            "points_expected": survey.reward_points or 0,
        }

    def _question_payload(self, question):
        options = [opt.label for opt in question.questionoption_set.all()]
        return {
            "id": self._public_qid(question.id),
            "type": question.type,
            "title": question.title,
            "options": options,
            "required": question.is_required,
            "order": question.order_no,
        }

    def _build_option_map(self, questions):
        option_map = {}
        for question in questions:
            options = list(question.questionoption_set.all())
            option_map[question.id] = {
                "labels": [opt.label for opt in options],
                "values": [opt.value for opt in options],
            }
        return option_map

    def _validate_answer(self, question, value, options):
        qtype = (question.type or "").lower()
        labels = set(options.get("labels", []))
        values = set(options.get("values", []))
        allowed = labels | values

        if qtype == "single":
            if isinstance(value, list):
                raise SurveyFillError(
                    422, f"invalid option for question {self._public_qid(question.id)}"
                )
            value_str = str(value)
            if allowed and value_str not in allowed:
                raise SurveyFillError(
                    422, f"invalid option for question {self._public_qid(question.id)}"
                )
        elif qtype == "multi":
            if not isinstance(value, list):
                raise SurveyFillError(
                    422, f"invalid option for question {self._public_qid(question.id)}"
                )
            for item in value:
                item_str = str(item)
                if allowed and item_str not in allowed:
                    raise SurveyFillError(
                        422,
                        f"invalid option for question {self._public_qid(question.id)}",
                    )
        elif qtype == "multi-text":
            if not isinstance(value, list):
                raise SurveyFillError(
                    422, f"invalid option for question {self._public_qid(question.id)}"
                )
            if options.get("labels") and len(value) != len(options.get("labels")):
                raise SurveyFillError(
                    422,
                    f"invalid option for question {self._public_qid(question.id)}",
                )
        elif qtype == "text":
            if isinstance(value, list):
                raise SurveyFillError(
                    422, f"invalid option for question {self._public_qid(question.id)}"
                )
        else:
            return

    def _normalize_answer_value(self, question, value):
        qtype = (question.type or "").lower()
        if qtype in ("multi", "multi-text"):
            return None, list(value)
        if isinstance(value, list):
            return None, value
        return str(value), None

    def _is_empty_answer(self, value):
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, list) and len(value) == 0:
            return True
        return False

    def _public_qid(self, question_id):
        return f"q_{question_id}"

    def _parse_int_id(self, value):
        if value is None:
            return None
        if isinstance(value, int):
            return value
        raw = str(value).strip()
        if not raw:
            return None
        match = re.search(r"\d+", raw)
        if not match:
            return None
        try:
            return int(match.group(0))
        except (TypeError, ValueError):
            return None

    def _parse_question_id(self, value):
        return self._parse_int_id(value)
