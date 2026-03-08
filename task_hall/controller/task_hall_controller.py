"""
Task Hall Controller - handles task hall endpoints.
"""

import json
import re

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.views import error, require_auth
from task_hall.service.task_hall_service import TaskHallError, TaskHallService


service = TaskHallService()


def _parse_json(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def _parse_int(value, default=None):
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_id_list(values):
    ids = []
    for value in values:
        if value is None:
            continue
        raw = str(value)
        match = re.search(r"\d+", raw)
        if match:
            try:
                ids.append(int(match.group(0)))
            except (TypeError, ValueError):
                continue
    return ids


@csrf_exempt
def task_hall_overview(request):
    if request.method != "GET":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    try:
        payload = service.get_overview(user)
        return JsonResponse(payload, status=200)
    except TaskHallError as exc:
        return error(exc.status, exc.message)
    except Exception as exc:
        return error(500, f"Internal server error: {str(exc)}")


@csrf_exempt
def task_hall_tasks(request):
    if request.method != "GET":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err

    filters = {
        "keyword": request.GET.get("keyword"),
        "type": request.GET.get("type"),
        "difficulty": _parse_int(request.GET.get("difficulty")),
        "min_reward": _parse_int(request.GET.get("min_reward")),
        "max_minutes": _parse_int(request.GET.get("max_minutes")),
        "status": request.GET.get("status"),
        "sort": request.GET.get("sort"),
        "page": _parse_int(request.GET.get("page"), default=1),
        "page_size": _parse_int(request.GET.get("page_size"), default=20),
    }
    try:
        payload = service.list_tasks(user, filters)
        return JsonResponse(payload, status=200)
    except TaskHallError as exc:
        return error(exc.status, exc.message)
    except Exception as exc:
        return error(500, f"Internal server error: {str(exc)}")


@csrf_exempt
def task_hall_refresh_batch(request):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    data = _parse_json(request)
    exclude_ids = _parse_id_list(data.get("exclude_task_ids") or [])
    batch_size = _parse_int(data.get("batch_size"), default=15)
    try:
        payload = service.refresh_batch(user, exclude_ids, batch_size)
        return JsonResponse(payload, status=200)
    except TaskHallError as exc:
        return error(exc.status, exc.message)
    except Exception as exc:
        return error(500, f"Internal server error: {str(exc)}")


@csrf_exempt
def task_hall_guest_tasks(request):
    """无需认证的访客随机任务接口，不调用 AI 推荐。"""
    if request.method != "GET":
        return error(405, "Method not allowed")
    size = _parse_int(request.GET.get("size"), default=15)
    size = max(1, min(size or 15, 30))  # 限制在 1-30 之间
    try:
        payload = service.get_guest_tasks(size)
        return JsonResponse(payload, status=200)
    except TaskHallError as exc:
        return error(exc.status, exc.message)
    except Exception as exc:
        return error(500, f"Internal server error: {str(exc)}")
