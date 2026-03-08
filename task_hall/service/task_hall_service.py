from datetime import timezone as dt_timezone
import random

from django.utils import timezone

from core.services.similarity_service import SimilarityService
from task_hall.mapper.task_hall_mapper import TaskHallMapper


class TaskHallError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


class TaskHallService:
    STATUS_LIVE_INTERNAL = {"published", "active", "live"}

    STATUS_FILTER_MAP = {
        "active": ["published", "active", "live"],
        "closed": ["paused", "closed", "ended", "expired", "rejected"],
        "full": ["published", "active", "live", "paused", "closed", "ended", "expired"],
    }

    def __init__(self):
        self.mapper = TaskHallMapper()

    def get_overview(self, user):
        notices = self.mapper.get_notices(user)
        summary = self._get_summary()
        filters = self.mapper.get_filters()
        return {
            "user": {
                "id": self._public_user_id(user.id),
                "nickname": user.nickname,
                "points": user.points,
            },
            "summary": summary,
            "filters": filters,
            "notices": notices,
        }

    def list_tasks(self, user, filters):
        normalized = self._normalize_filters(filters)
        queryset = (
            self.mapper.list_surveys(normalized)
            .exclude(owner=user)
            .exclude(response__user=user)
            .distinct()
        )
        # 只返回当前有已发布问卷内容的可填写任务
        queryset = queryset.filter(active_questionnaire__status="published")
        total = queryset.count()

        page = max(normalized.get("page", 1), 1)
        page_size = min(max(normalized.get("page_size", 20), 1), 50)
        offset = (page - 1) * page_size

        items = self._list_personalized_items(user.id, queryset, offset, page_size)
        return {
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def refresh_batch(self, user, exclude_task_ids, batch_size):
        normalized = {"status": list(self.STATUS_LIVE_INTERNAL)}
        queryset = (
            self.mapper.list_surveys(normalized)
            .exclude(owner=user)
            .exclude(response__user=user)
            .distinct()
        )
        # 只返回当前有已发布问卷内容的可填写任务
        queryset = queryset.filter(active_questionnaire__status="published")

        size = max(batch_size or 0, 0)
        items = self._list_personalized_items(
            user.id,
            queryset,
            offset=0,
            page_size=size,
            exclude_task_ids=exclude_task_ids,
        )
        return {"items": items}

    def _list_personalized_items(
        self, user_id, queryset, offset, page_size, exclude_task_ids=None
    ):
        survey_ids = list(queryset.values_list("id", flat=True))
        ranked = SimilarityService.rank_candidate_surveys_for_user(
            user_id=str(user_id),
            candidate_survey_ids=survey_ids,
            exclude_ids=exclude_task_ids,
        )

        # 当 ranked 为空，或全部结果 score == 0（无有效个性化信息）时，降级走 fallback
        # 这样与"换一批"在排除所有已见问卷后走 fallback 的体验保持一致
        has_meaningful_rank = ranked and any(
            item.get("score", 0.0) > 0.0 for item in ranked
        )

        if not has_meaningful_rank:
            fallback = list(
                queryset.order_by("-created_at")[offset : offset + page_size]
            )
            filled_counts = self.mapper.get_filled_counts(
                [survey.id for survey in fallback]
            )
            return [
                self._to_task_card(survey, filled_counts.get(survey.id, 0))
                for survey in fallback
            ]

        window = ranked[offset : offset + page_size]
        id_order = [item["survey_id"] for item in window]
        survey_by_id = {
            s.id: s for s in queryset.filter(id__in=id_order).select_related("owner")
        }
        filled_counts = self.mapper.get_filled_counts(id_order)

        items = []
        for item in window:
            survey = survey_by_id.get(item["survey_id"])
            if not survey:
                continue
            items.append(
                self._to_task_card(
                    survey,
                    filled_counts.get(survey.id, 0),
                    match_score=float(item.get("score", 0.0)),
                    match_reason=item.get("reason", ""),
                )
            )
        return items

    def _get_summary(self):
        # 仅统计那些处于可投放且有已发布问卷内容的问卷
        queryset = self.mapper.base_queryset().filter(
            status__in=self.STATUS_LIVE_INTERNAL,
            active_questionnaire__status="published",
        )
        total = queryset.count()
        today = timezone.now().date()
        new_today = queryset.filter(created_at__date=today).count()
        return {
            "available_tasks": total,
            "new_tasks_today": new_today,
            "high_match_tasks": 0,
        }

    def _normalize_filters(self, filters):
        status = (filters.get("status") or "").strip()
        mapped_status = None
        if status:
            mapped_status = self.STATUS_FILTER_MAP.get(status)
            if not mapped_status:
                raise TaskHallError(422, "invalid status")
        if not mapped_status:
            mapped_status = list(self.STATUS_LIVE_INTERNAL)
        return {
            "keyword": (filters.get("keyword") or "").strip(),
            "type": (filters.get("type") or "").strip(),
            "difficulty": filters.get("difficulty"),
            "min_reward": filters.get("min_reward"),
            "max_minutes": filters.get("max_minutes"),
            "status": mapped_status,
            "sort": (filters.get("sort") or "").strip(),
            "page": filters.get("page", 1),
            "page_size": filters.get("page_size", 20),
        }

    def _to_task_card(self, survey, filled_count=0, match_score=None, match_reason=""):
        difficulty = survey.difficulty or 3
        reward = survey.reward_points or 0

        target = survey.target or 0
        status = "active" if survey.status in self.STATUS_LIVE_INTERNAL else "closed"
        if target and filled_count >= target:
            status = "full"

        if match_score is None:
            ratio = reward / difficulty if difficulty else 0
            if ratio >= 1.5:
                match_level = "high"
            elif ratio >= 1:
                match_level = "medium"
            else:
                match_level = "low"
            match_reason = match_reason or ""
        else:
            if match_score >= 0.45:
                match_level = "high"
            elif match_score >= 0.2:
                match_level = "medium"
            else:
                match_level = "low"
            if not match_reason:
                match_reason = "基于你的标签偏好推荐"

        return {
            "id": self._public_survey_id(survey.id),
            "title": survey.title,
            "subtitle": survey.description or "",
            "sender": survey.owner.nickname if survey.owner else "匿名",
            "type": self.mapper.get_task_type(survey.id),
            "estimated": survey.estimated_minutes or 0,
            "difficulty": difficulty,
            "reward": reward,
            "filled": filled_count,
            "total": target,
            "deadline": self._iso_str(survey.deadline) if survey.deadline else None,
            "status": status,
            "match_level": match_level,
            "match_reason": match_reason,
        }

    def _public_survey_id(self, survey_id):
        return f"s_{survey_id}"

    def _public_user_id(self, user_id):
        return f"u_{user_id}"

    def _iso_str(self, dt):
        if not dt:
            return None
        return dt.astimezone(dt_timezone.utc).isoformat().replace("+00:00", "Z")

    def get_guest_tasks(self, size=15):
        """
        无需认证的访客接口：随机返回若干已发布问卷，不调用 AI 推荐。
        先获取所有符合条件的 ID，再在 Python 层随机抽样，避免 ORDER BY RAND() 全表扫描。
        """
        queryset = self.mapper.base_queryset().filter(
            status__in=self.STATUS_LIVE_INTERNAL,
            active_questionnaire__status="published",
        )
        all_ids = list(queryset.values_list("id", flat=True))
        if not all_ids:
            return {"items": []}

        sample_size = min(size, len(all_ids))
        sampled_ids = random.sample(all_ids, sample_size)

        surveys = {s.id: s for s in queryset.filter(id__in=sampled_ids).select_related("owner")}
        filled_counts = self.mapper.get_filled_counts(sampled_ids)

        items = [
            self._to_task_card(surveys[sid], filled_counts.get(sid, 0))
            for sid in sampled_ids
            if sid in surveys
        ]
        return {"items": items}
