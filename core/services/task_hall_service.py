from core.managers.task_hall_manager import TaskHallManager
from core.services.similarity_service import SimilarityService
from core.models import Survey


class TaskHallService:
    @staticmethod
    def get_overview(user):
        notices = TaskHallManager.get_notices(user)
        summary = TaskHallManager.get_summary()
        filters = TaskHallManager.get_filters()
        return {
            "user": {
                "id": str(user.id),
                "nickname": user.nickname,
                "points": user.points,
            },
            "summary": summary,
            "filters": filters,
            "notices": notices,
        }

    @staticmethod
    def list_tasks(user, filters):
        # Use personalized recommendation when a user is present: call internal recommend API
        page = filters.get("page", 1)
        page_size = filters.get("page_size", 20)
        try:
            if user:
                # request top `page_size` recommendations for user
                recs = SimilarityService.recommend_surveys_for_user(str(user.id), page_size)
                ids = [int(item["id"]) for item in recs]
                items = []
                # preserve order of recommendations
                for sid in ids:
                    s = Survey.objects.filter(id=sid).select_related("owner").first()
                    if not s:
                        continue
                    filled = TaskHallManager._get_filled_counts([s.id]).get(s.id, 0)
                    items.append(TaskHallManager._to_task_card(s, filled))
                total = len(items)
                return {"items": items, "page": page, "page_size": page_size, "total": total}
        except Exception:
            # fallback to non-personalized listing on failure
            pass

        items, total = TaskHallManager.list_tasks(filters)
        return {"items": items, "page": page, "page_size": page_size, "total": total}

    @staticmethod
    def refresh_batch(user, exclude_task_ids, batch_size):
        # Use recommendation to provide personalized replacements when possible
        try:
            if user:
                recs = SimilarityService.recommend_surveys_for_user(str(user.id), max(batch_size, 1))
                # filter out excluded ids and return up to batch_size
                filtered = [r for r in recs if str(r.get("id")) not in [str(x) for x in (exclude_task_ids or [])]]
                ids = [int(r.get("id")) for r in filtered][:batch_size]
                items = []
                for sid in ids:
                    s = Survey.objects.filter(id=sid).select_related("owner").first()
                    if not s:
                        continue
                    filled = TaskHallManager._get_filled_counts([s.id]).get(s.id, 0)
                    items.append(TaskHallManager._to_task_card(s, filled))
                return {"items": items}
        except Exception:
            # fallback
            pass

        items = TaskHallManager.refresh_batch(exclude_task_ids, batch_size)
        return {"items": items}
