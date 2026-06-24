import time

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from core import views


def healthz(request):
    """后端健康检查：进程、数据库、缓存可用性。"""
    checks = {}
    overall_ok = True

    # 应用进程存活
    checks["app"] = {"ok": True}

    # MySQL 连通性检查
    db_start = time.perf_counter()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks["db"] = {
            "ok": True,
            "latency_ms": round((time.perf_counter() - db_start) * 1000, 2),
        }
    except Exception as exc:
        overall_ok = False
        checks["db"] = {
            "ok": False,
            "error": "unhealthy",
        }

    # Redis 连通性检查
    cache_start = time.perf_counter()
    cache_key = "healthz:redis"
    cache_value = "ok"
    try:
        cache.set(cache_key, cache_value, 10)
        got = cache.get(cache_key)
        if got != cache_value:
            raise ValueError("cache roundtrip mismatch")
        checks["redis"] = {
            "ok": True,
            "latency_ms": round((time.perf_counter() - cache_start) * 1000, 2),
        }
    except Exception as exc:
        overall_ok = False
        checks["redis"] = {
            "ok": False,
            "error": "unhealthy",
        }

    status = 200 if overall_ok else 503
    return JsonResponse(
        {
            "ok": overall_ok,
            "checks": checks,
        },
        status=status,
    )


urlpatterns = [
    path("", views.index),
    path("healthz", healthz),
    path("api/v1/", include("core.urls")),
    path("api/v1/", include("personal_homepage.urls")),
    path("api/v1/", include("survey_management.urls")),
    path("api/v1/", include("task_hall.urls")),
    path("api/v1/", include("team_messaging.urls")),
    path("api/v1/points/", include("points_record.urls")),
    path("api/v1/profile/", include("user_profile_extractor.urls")),
    path("api/v1/admin/", include("admin_backend.urls")),
]
