from django.urls import path, include
from django.http import HttpResponse
from core import views


def healthz(request):
    # 简单的健康检查端点，返回 HTTP 200 表示服务存活
    return HttpResponse("ok")


urlpatterns = [
    path("", views.index),
    path("healthz", healthz),
    path("api/v1/", include("core.urls")),
    path("api/v1/", include("personal_homepage.urls")),
    path("api/v1/", include("survey_management.urls")),
    path("api/v1/", include("task_hall.urls")),
    path("api/v1/points/", include("points_record.urls")),
    path("api/v1/profile/", include("user_profile_extractor.urls")),
]
