from django.db.models import Count, Q
from django.utils import timezone

from core.models import Notification, Response, Survey, SurveyTag, Tag


class TaskHallManager:
    @staticmethod
    def _base_queryset():
        return Survey.objects.select_related("owner")

    @staticmethod
    def _apply_filters(queryset, filters):
        keyword = filters.get("keyword")
        if keyword:
            queryset = queryset.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword))
        status = filters.get("status")
        if status:
            queryset = queryset.filter(status=status)
        min_reward = filters.get("min_reward")
        if min_reward is not None:
            queryset = queryset.filter(reward_points__gte=min_reward)
        max_minutes = filters.get("max_minutes")
        if max_minutes is not None:
            queryset = queryset.filter(estimated_minutes__lte=max_minutes)
        difficulty = filters.get("difficulty")
        if difficulty is not None:
            queryset = queryset.filter(difficulty=difficulty)
        return queryset

    @staticmethod
    def _task_type_for_survey(survey_id):
        tag = (
            SurveyTag.objects.select_related("tag")
            .filter(survey_id=survey_id)
            .order_by("id")
            .first()
        )
        return tag.tag.name if tag else "未分类"

    @staticmethod
    def _to_task_card(survey, filled_count=0):
        difficulty = survey.difficulty or 3
        reward = survey.reward_points or 0
        ratio = reward / difficulty if difficulty else 0
        if ratio >= 1.5:
            match_level = "high"
        elif ratio >= 1:
            match_level = "medium"
        else:
            match_level = "low"
        return {
            "id": str(survey.id),
            "title": survey.title,
            "subtitle": survey.description or "",
            "sender": survey.owner.nickname if survey.owner else "匿名",
            "type": TaskHallManager._task_type_for_survey(survey.id),
            "estimated": survey.estimated_minutes or 0,
            "difficulty": difficulty,
            "reward": reward,
            "filled": filled_count,
            "total": survey.target or 0,
            "deadline": survey.deadline.isoformat().replace("+00:00", "Z") if survey.deadline else None,
            "status": survey.status,
            "match_level": match_level,
            "match_reason": "",
        }

    @staticmethod
    def list_tasks(filters):
        queryset = TaskHallManager._apply_filters(TaskHallManager._base_queryset(), filters)
        total = queryset.count()
        page = max(filters.get("page", 1), 1)
        page_size = min(max(filters.get("page_size", 20), 1), 50)
        offset = (page - 1) * page_size
        surveys = list(queryset.order_by("-created_at")[offset : offset + page_size])
        filled_counts = TaskHallManager._get_filled_counts([survey.id for survey in surveys])
        items = [
            TaskHallManager._to_task_card(survey, filled_counts.get(survey.id, 0))
            for survey in surveys
        ]
        return items, total

    @staticmethod
    def refresh_batch(exclude_task_ids, batch_size):
        queryset = TaskHallManager._base_queryset()
        if exclude_task_ids:
            queryset = queryset.exclude(id__in=exclude_task_ids)
        surveys = list(queryset.order_by("-created_at")[: batch_size or 0])
        filled_counts = TaskHallManager._get_filled_counts([survey.id for survey in surveys])
        items = [
            TaskHallManager._to_task_card(survey, filled_counts.get(survey.id, 0))
            for survey in surveys
        ]
        return items

    @staticmethod
    def _get_filled_counts(survey_ids):
        if not survey_ids:
            return {}
        rows = (
            Response.objects.filter(survey_id__in=survey_ids, submitted_at__isnull=False)
            .values("survey_id")
            .annotate(cnt=Count("id"))
        )
        return {row["survey_id"]: row["cnt"] for row in rows}

    @staticmethod
    def get_summary():
        total = TaskHallManager._base_queryset().count()
        today = timezone.now().date()
        new_today = TaskHallManager._base_queryset().filter(created_at__date=today).count()
        return {
            "available_tasks": total,
            "new_tasks_today": new_today,
            "high_match_tasks": 0,
        }

    @staticmethod
    def get_filters():
        types = list(Tag.objects.filter(type=Tag.TYPE_SURVEY).values_list("name", flat=True))
        return {"types": types, "difficulties": [1, 2, 3, 4, 5]}

    @staticmethod
    def get_notices(user, limit=3):
        notices = Notification.objects.filter(user=user).order_by("-created_at")[:limit]
        return [
            {
                "id": str(notice.id),
                "title": notice.title,
                "content": notice.content,
                "created_at": notice.created_at.isoformat().replace("+00:00", "Z"),
            }
            for notice in notices
        ]
