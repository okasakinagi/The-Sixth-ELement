"""
Analytics Mapper — 数据分析模块的数据库查询层
"""

from django.db.models import Avg, Count

from core.models import Answer, Question, QuestionOption, Response, Survey, UserRole


class AnalyticsMapper:
    # ─── 问卷与权限 ──────────────────────────────────

    @staticmethod
    def get_survey(survey_id):
        """按 ID 获取问卷，同时预加载 active_questionnaire。"""
        return (
            Survey.objects.select_related("owner", "active_questionnaire")
            .filter(id=survey_id)
            .first()
        )

    @staticmethod
    def is_admin(user):
        """判断用户是否拥有 admin 角色。"""
        return UserRole.objects.filter(user=user, role__name="admin").exists()

    # ─── 总览统计 ────────────────────────────────────

    @staticmethod
    def get_responses_count(survey_id):
        """已提交的答卷数（submitted_at 不为空即视为已提交）。"""
        return Response.objects.filter(
            survey_id=survey_id, submitted_at__isnull=False
        ).count()

    @staticmethod
    def get_avg_duration(survey_id):
        """已提交答卷的平均作答时长（秒），无数据时返回 None。"""
        result = Response.objects.filter(
            survey_id=survey_id,
            submitted_at__isnull=False,
            duration_seconds__isnull=False,
        ).aggregate(avg=Avg("duration_seconds"))
        avg = result.get("avg")
        return round(avg) if avg is not None else None

    # ─── 题目统计 ────────────────────────────────────

    @staticmethod
    def get_questions_with_options(questionnaire_id):
        """获取问卷下所有题目，并预取选项，按 order_no 排序。"""
        questions = list(
            Question.objects.filter(questionnaire_id=questionnaire_id).order_by(
                "order_no", "id"
            )
        )
        # 预取选项，减少 N+1
        qids = [q.id for q in questions]
        opts = list(
            QuestionOption.objects.filter(question_id__in=qids).order_by(
                "question_id", "order_no"
            )
        )
        opt_map = {}
        for opt in opts:
            opt_map.setdefault(opt.question_id, []).append(opt)
        for q in questions:
            q._prefetched_options = opt_map.get(q.id, [])
        return questions

    @staticmethod
    def get_choice_answers(question_id):
        """
        获取某题的所有已提交答案（单选/多选统计用）。
        返回 Answer queryset，只取 value_text 和 value_json。
        """
        return list(
            Answer.objects.filter(
                question_id=question_id,
                response__submitted_at__isnull=False,
            ).values("value_text", "value_json")
        )

    @staticmethod
    def get_text_answers(question_id, page, page_size):
        """
        获取填空题的文本回答，按 submitted_at 倒序，支持分页。
        返回 (items: list[dict], total: int)
        """
        qs = (
            Answer.objects.filter(
                question_id=question_id,
                response__submitted_at__isnull=False,
            )
            .select_related("response__user")
            .order_by("-response__submitted_at")
        )

        total = qs.count()
        offset = (page - 1) * page_size
        rows = qs[offset : offset + page_size]

        items = []
        for answer in rows:
            user = answer.response.user
            items.append(
                {
                    "response_id": f"r_{answer.response_id}",
                    "nickname": user.nickname if user else "",
                    "value_text": answer.value_text,
                    "value_json": answer.value_json,
                    "submitted_at": answer.response.submitted_at,
                }
            )
        return items, total

    # ─── 导出 ────────────────────────────────────────

    @staticmethod
    def get_export_responses(survey_id):
        """获取所有已提交答卷，预加载用户信息，按提交时间排序。"""
        return list(
            Response.objects.filter(survey_id=survey_id, submitted_at__isnull=False)
            .select_related("user")
            .order_by("submitted_at")
        )

    @staticmethod
    def get_export_answers(response_ids):
        """批量获取答案，预加载题目信息。"""
        return list(
            Answer.objects.filter(response_id__in=response_ids).select_related(
                "question"
            )
        )
