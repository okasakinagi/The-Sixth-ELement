"""
SurveyFill Service - 业务逻辑层
处理问卷填写的校验、格式转换与提交
"""

import re
from django.db import transaction
from django.utils import timezone

from core.models import PointsLog, TeamMember
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
            raise SurveyFillError(422, "无效的问卷ID")
        survey = self.mapper.get_survey(survey_pk)
        if not survey:
            raise SurveyFillError(404, "未找到该问卷")
        if survey.status != "published":
            raise SurveyFillError(422, "问卷未处于可填写状态")
        questionnaire = survey.active_questionnaire
        if not questionnaire or questionnaire.status != "published":
            raise SurveyFillError(422, "问卷内容尚未准备好，请稍后再试")

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
            raise SurveyFillError(422, "无效的问卷ID")
        survey = self.mapper.get_survey(survey_pk)
        if not survey:
            raise SurveyFillError(404, "未找到该问卷")
        if survey.status != "published":
            raise SurveyFillError(422, "问卷未处于可填写状态")
        if survey.owner_id == user.id:
            raise SurveyFillError(422, "不能填写自己发布的问卷")
        if self.mapper.response_exists(survey.id, user.id):
            raise SurveyFillError(422, "您已提交过该问卷")

        questionnaire = survey.active_questionnaire
        if not questionnaire or questionnaire.status != "published":
            raise SurveyFillError(422, "问卷内容尚未准备好，请稍后再试")

        duration_seconds = data.get("duration_seconds")
        if duration_seconds is None:
            raise SurveyFillError(422, "需要提供填写时长(duration_seconds)")
        try:
            duration_seconds = int(duration_seconds)
        except (TypeError, ValueError):
            raise SurveyFillError(422, "填写时长必须为数字")
        if duration_seconds < 10:
            raise SurveyFillError(422, "填写时长过短，请完整填写后提交")

        answers = data.get("answers")
        if not isinstance(answers, list):
            raise SurveyFillError(422, "需要提供答案列表(answers)")

        questions = list(self.mapper.get_questions(questionnaire.id))
        question_map = {q.id: q for q in questions}
        option_map = self._build_option_map(questions)

        answer_map = {}
        for item in answers:
            if not isinstance(item, dict):
                raise SurveyFillError(422, "答案格式无效")
            question_id = self._parse_question_id(item.get("question_id"))
            if question_id is None:
                raise SurveyFillError(422, "无效的问题ID")
            if question_id not in question_map:
                raise SurveyFillError(
                    422, f"未找到问题 {self._public_qid(question_id)}"
                )
            answer_map[question_id] = item.get("value")

        for question in questions:
            qid = question.id
            value = answer_map.get(qid)
            if question.is_required and self._is_empty_answer(value):
                raise SurveyFillError(422, f"问题 {self._public_qid(qid)} 为必答题")

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

        # 提交即时发放积分（已取消审核机制）
        reward = survey.reward_points or 0
        points_receiver_id = user.id
        points_receiver_nickname = user.nickname
        points_flow = "self"
        points_flow_message = "积分已到账"

        joined_team_member = (
            TeamMember.objects.select_related("team", "team__owner")
            .filter(user_id=user.id, status="joined", team__status="active")
            .first()
        )

        if joined_team_member and joined_team_member.team.owner_id != user.id:
            points_receiver_id = joined_team_member.team.owner_id
            points_receiver_nickname = joined_team_member.team.owner.nickname
            points_flow = "team_owner"
            points_flow_message = (
                f"你已加入队伍，积分已自动入账到队长 {points_receiver_nickname}"
            )

        if reward > 0:
            with transaction.atomic():
                user_obj = user.__class__.objects.select_for_update().get(pk=user.pk)
                user_obj.activity_points += reward
                if points_receiver_id == user_obj.id:
                    user_obj.points += reward
                    user_obj.save(update_fields=["points", "activity_points"])
                    PointsLog.objects.create(
                        user=user_obj,
                        points_type="fill_reward",
                        delta=reward,
                        reason=f"填写问卷《{survey.title}》奖励",
                        ref_type="survey",
                        ref_id=survey.id,
                    )
                else:
                    user_obj.save(update_fields=["activity_points"])
                    receiver_obj = user.__class__.objects.select_for_update().get(
                        pk=points_receiver_id
                    )
                    receiver_obj.points += reward
                    receiver_obj.save(update_fields=["points"])
                    PointsLog.objects.create(
                        user=receiver_obj,
                        points_type="fill_reward",
                        delta=reward,
                        reason=(
                            f"队员 {user_obj.nickname} 填写问卷《{survey.title}》奖励入账"
                        ),
                        ref_type="survey",
                        ref_id=survey.id,
                    )
                    PointsLog.objects.create(
                        user=user_obj,
                        points_type="fill_reward",
                        delta=0,
                        reason=(
                            f"填写问卷《{survey.title}》完成，积分已转入队长 {receiver_obj.nickname}"
                        ),
                        ref_type="survey",
                        ref_id=survey.id,
                    )
            points_awarded = reward
        else:
            points_awarded = 0

        # 更新任务进度（捕获异常，不影响主流程）
        try:
            from task_hall.service.level_service import LevelService
            LevelService.on_fill_submitted(user)
        except Exception:
            pass

        return {
            "id": str(response.id),
            "status": response.status,
            "points_awarded": points_awarded,
            "points_expected": reward,
            "points_receiver_id": points_receiver_id,
            "points_receiver_nickname": points_receiver_nickname,
            "points_flow": points_flow,
            "points_flow_message": points_flow_message,
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
                    422, f"问题 {self._public_qid(question.id)} 的答案无效"
                )
            value_str = str(value)
            if allowed and value_str not in allowed:
                raise SurveyFillError(
                    422, f"问题 {self._public_qid(question.id)} 的答案无效"
                )
        elif qtype == "multi":
            if not isinstance(value, list):
                raise SurveyFillError(
                    422, f"问题 {self._public_qid(question.id)} 的答案无效"
                )
            for item in value:
                item_str = str(item)
                if allowed and item_str not in allowed:
                    raise SurveyFillError(
                        422, f"问题 {self._public_qid(question.id)} 的答案无效"
                    )
        elif qtype == "multi-text":
            if not isinstance(value, list):
                raise SurveyFillError(
                    422, f"问题 {self._public_qid(question.id)} 的答案无效"
                )
            if options.get("labels") and len(value) != len(options.get("labels")):
                raise SurveyFillError(
                    422, f"问题 {self._public_qid(question.id)} 的答案无效"
                )
        elif qtype == "text":
            if isinstance(value, list):
                raise SurveyFillError(
                    422, f"问题 {self._public_qid(question.id)} 的答案无效"
                )
        else:
            return
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
