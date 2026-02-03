from django.db.models import Count, Q

from core.models import Notification, Response, Survey, SurveyTag, Tag


class TaskHallMapper:
    @staticmethod
    def base_queryset():
        return Survey.objects.select_related("owner")

    @staticmethod
    def list_surveys(filters):
        queryset = TaskHallMapper._apply_filters(TaskHallMapper.base_queryset(), filters)
        return queryset

    @staticmethod
    def _apply_filters(queryset, filters):
        keyword = filters.get("keyword")
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword)
                | Q(description__icontains=keyword)
                | Q(owner__nickname__icontains=keyword)
            )
        task_type = filters.get("type")
        if task_type:
            queryset = queryset.filter(surveytag__tag__name=task_type).distinct()
        status = filters.get("status")
        if status:
            queryset = queryset.filter(status__in=status)
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
    def get_task_type(survey_id):
        tag = (
            SurveyTag.objects.select_related("tag")
            .filter(survey_id=survey_id)
            .order_by("id")
            .first()
        )
        return tag.tag.name if tag else "未分类"

    @staticmethod
    def get_filled_counts(survey_ids):
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
    def get_filters():
        types = list(
            Tag.objects.filter(type=Tag.TYPE_SURVEY).values_list("name", flat=True)
        )
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
