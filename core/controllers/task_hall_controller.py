import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.services.task_hall_service import TaskHallService
from core.views import error, require_auth


def parse_json(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def parse_int(value, default=None):
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@csrf_exempt
def task_hall_overview(request):
    if request.method != "GET":
        return error(405, "Method not allowed")
    user, resp = require_auth(request)
    if resp:
        return resp
    payload = TaskHallService.get_overview(user)
    return JsonResponse(payload)


@csrf_exempt
def task_hall_tasks(request):
    if request.method != "GET":
        return error(405, "Method not allowed")
    user, resp = require_auth(request)
    if resp:
        return resp
    params = request.GET
    filters = {
        "keyword": params.get("keyword", "").strip(),
        "type": params.get("type", "").strip(),
        "difficulty": parse_int(params.get("difficulty")),
        "min_reward": parse_int(params.get("min_reward")),
        "max_minutes": parse_int(params.get("max_minutes")),
        "status": params.get("status", "").strip(),
        "sort": params.get("sort", "").strip(),
        "page": parse_int(params.get("page"), default=1),
        "page_size": parse_int(params.get("page_size"), default=20),
    }
    payload = TaskHallService.list_tasks(user, filters)
    return JsonResponse(payload)


@csrf_exempt
def task_hall_refresh_batch(request):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, resp = require_auth(request)
    if resp:
        return resp
    data = parse_json(request)
    exclude_ids = data.get("exclude_task_ids") or []
    batch_size = parse_int(data.get("batch_size"), default=15)
    payload = TaskHallService.refresh_batch(user, exclude_ids, batch_size)
    return JsonResponse(payload)
