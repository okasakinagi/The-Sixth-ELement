"""
Analytics Controller — 数据分析模块的 HTTP 处理层
"""

import re
from datetime import datetime, timezone as dt_timezone

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.views import error, require_auth
from survey_management.service.analytics_service import AnalyticsError, AnalyticsService

_service = AnalyticsService()


def _parse_survey_id(value):
    """将 's_2001' / '2001' / 2001 统一解析为整数，失败返回 None。"""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    m = re.search(r"\d+", str(value))
    if not m:
        return None
    try:
        return int(m.group(0))
    except (TypeError, ValueError):
        return None


def _slugify(text):
    """把问卷标题转换为适合文件名的字符串（保留中文、字母、数字，空格转下划线）。"""
    text = re.sub(r"[\\/:*?\"<>|]", "", text or "survey")
    text = re.sub(r"\s+", "_", text.strip())
    return text[:60] or "survey"


@csrf_exempt
def analytics_summary(request, survey_id):
    """GET /surveys/{id}/analytics/summary"""
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)

    user, err = require_auth(request)
    if err:
        return err

    pk = _parse_survey_id(survey_id)
    if pk is None:
        return JsonResponse({"error": "invalid survey id"}, status=422)

    try:
        data = _service.get_summary(user, pk)
        return JsonResponse(data)
    except AnalyticsError as e:
        return error(e.status, e.message)
    except Exception:
        return JsonResponse({"error": "internal server error"}, status=500)


@csrf_exempt
def analytics_questions(request, survey_id):
    """GET /surveys/{id}/analytics/questions?text_page=1&text_page_size=20"""
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)

    user, err = require_auth(request)
    if err:
        return err

    pk = _parse_survey_id(survey_id)
    if pk is None:
        return JsonResponse({"error": "invalid survey id"}, status=422)

    try:
        text_page = int(request.GET.get("text_page", 1))
        text_page_size = int(request.GET.get("text_page_size", 20))
    except (TypeError, ValueError):
        return JsonResponse({"error": "invalid pagination params"}, status=422)

    try:
        data = _service.get_questions_stats(user, pk, text_page, text_page_size)
        return JsonResponse(data)
    except AnalyticsError as e:
        return error(e.status, e.message)
    except Exception:
        return JsonResponse({"error": "internal server error"}, status=500)


@csrf_exempt
def analytics_export(request, survey_id):
    """GET /surveys/{id}/analytics/export?format=csv|xlsx"""
    if request.method != "GET":
        return JsonResponse({"error": "method not allowed"}, status=405)

    user, err = require_auth(request)
    if err:
        return err

    pk = _parse_survey_id(survey_id)
    if pk is None:
        return JsonResponse({"error": "invalid survey id"}, status=422)

    fmt = request.GET.get("format", "csv").lower()
    if fmt not in ("csv", "xlsx"):
        return JsonResponse({"error": "format must be csv or xlsx"}, status=422)

    try:
        ts = datetime.now(dt_timezone.utc).strftime("%Y%m%d_%H%M%S")
        if fmt == "csv":
            content_bytes, title = _service.export_csv(user, pk)
            filename = f"{_slugify(title)}_{ts}.csv"
            response = HttpResponse(
                content_bytes, content_type="text/csv; charset=utf-8"
            )
        else:
            content_bytes, title = _service.export_xlsx(user, pk)
            filename = f"{_slugify(title)}_{ts}.xlsx"
            response = HttpResponse(
                content_bytes,
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except AnalyticsError as e:
        return error(e.status, e.message)
    except Exception:
        return JsonResponse({"error": "internal server error"}, status=500)
