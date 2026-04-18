from django.urls import path

from task_hall.controller import task_hall_controller, level_controller


urlpatterns = [
    path("task-hall/home-modules", task_hall_controller.task_hall_home_modules),
    path("task-hall/overview", task_hall_controller.task_hall_overview),
    path("task-hall/tasks", task_hall_controller.task_hall_tasks),
    path("task-hall/batch/refresh", task_hall_controller.task_hall_refresh_batch),
    path("task-hall/guest-tasks", task_hall_controller.task_hall_guest_tasks),
    path(
        "task-hall/daily-recommendations",
        task_hall_controller.task_hall_daily_recommendations,
    ),
    path(
        "task-hall/daily-recommendations/<str:survey_id>/claim-bonus",
        task_hall_controller.task_hall_claim_daily_bonus,
    ),
    # 等级与任务
    path("user/level", level_controller.get_level),
    path("tasks/daily", level_controller.get_daily_tasks),
    path("tasks/weekly", level_controller.get_weekly_tasks),
    path("tasks/<str:task_code>/claim", level_controller.claim_task),
]
