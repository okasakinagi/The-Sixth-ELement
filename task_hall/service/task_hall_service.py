from django.utils import timezone

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
        total = queryset.count()

        page = max(normalized.get("page", 1), 1)
        page_size = min(max(normalized.get("page_size", 20), 1), 50)
        offset = (page - 1) * page_size

        ordering = self._ordering_for_sort(normalized.get("sort"))
        surveys = list(queryset.order_by(*ordering)[offset : offset + page_size])
        filled_counts = self.mapper.get_filled_counts([survey.id for survey in surveys])

        items = [
            self._to_task_card(survey, filled_counts.get(survey.id, 0))
            for survey in surveys
        ]
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
        if exclude_task_ids:
            queryset = queryset.exclude(id__in=exclude_task_ids)
        surveys = list(queryset.order_by("-created_at")[: batch_size or 0])
        filled_counts = self.mapper.get_filled_counts([survey.id for survey in surveys])
        items = [
            self._to_task_card(survey, filled_counts.get(survey.id, 0))
            for survey in surveys
        ]
        return {"items": items}

    def _get_summary(self):
        queryset = self.mapper.base_queryset().filter(status__in=self.STATUS_LIVE_INTERNAL)
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

    def _ordering_for_sort(self, sort):
        if sort == "reward_desc":
            return ("-reward_points", "-created_at")
        if sort == "ending":
            return ("deadline", "-created_at")
        if sort == "newest":
            return ("-created_at",)
        if sort == "recommend":
            return ("-reward_points", "difficulty", "-created_at")
        return ("-created_at",)

    def _to_task_card(self, survey, filled_count=0):
        difficulty = survey.difficulty or 3
        reward = survey.reward_points or 0
        ratio = reward / difficulty if difficulty else 0
        if ratio >= 1.5:
            match_level = "high"
        elif ratio >= 1:
            match_level = "medium"
        else:
            match_level = "low"

        target = survey.target or 0
        status = "active" if survey.status in self.STATUS_LIVE_INTERNAL else "closed"
        if target and filled_count >= target:
            status = "full"

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
            "match_reason": "",
        }

    def _public_survey_id(self, survey_id):
        return f"s_{survey_id}"

    def _public_user_id(self, user_id):
        return f"u_{user_id}"

    def _iso_str(self, dt):
        if not dt:
            return None
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
