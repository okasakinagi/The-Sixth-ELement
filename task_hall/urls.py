from django.urls import path

from task_hall.controller import task_hall_controller


urlpatterns = [
    path("task-hall/overview", task_hall_controller.task_hall_overview),
    path("task-hall/tasks", task_hall_controller.task_hall_tasks),
    path("task-hall/batch/refresh", task_hall_controller.task_hall_refresh_batch),
    path("task-hall/guest-tasks", task_hall_controller.task_hall_guest_tasks),
]
