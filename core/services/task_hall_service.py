from core.managers.task_hall_manager import TaskHallManager


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
        items, total = TaskHallManager.list_tasks(filters)
        return {
            "items": items,
            "page": filters.get("page", 1),
            "page_size": filters.get("page_size", 20),
            "total": total,
        }

    @staticmethod
    def refresh_batch(user, exclude_task_ids, batch_size):
        items = TaskHallManager.refresh_batch(exclude_task_ids, batch_size)
        return {"items": items}
