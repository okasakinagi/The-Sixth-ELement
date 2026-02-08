from django.urls import path

from points_record.controller.points_record_controller import points_summary, points_logs, update_points

urlpatterns = [
    path("summary", points_summary, name="points_summary"),
    path("logs", points_logs, name="points_logs"),
    path("update", update_points, name="update_points"),
]
