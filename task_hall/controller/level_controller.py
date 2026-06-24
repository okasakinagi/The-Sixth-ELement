"""
Level & Task Controller – 等级查询与任务领取接口
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.views import error, internal_error, require_auth
from task_hall.service.level_service import LevelService, LevelServiceError


def _parse_json(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


@csrf_exempt
def get_level(request):
    """GET /api/v1/user/level — 查询当前用户等级/EXP/称号"""
    if request.method != "GET":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    try:
        payload = LevelService.get_level_info(user)
        return JsonResponse(payload, status=200)
    except Exception as exc:
        return internal_error(exc)


@csrf_exempt
def get_daily_tasks(request):
    """GET /api/v1/tasks/daily — 今日任务列表与进度"""
    if request.method != "GET":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    try:
        payload = LevelService.get_daily_tasks(user)
        return JsonResponse(payload, status=200)
    except Exception as exc:
        return internal_error(exc)


@csrf_exempt
def get_weekly_tasks(request):
    """GET /api/v1/tasks/weekly — 本周任务列表与进度"""
    if request.method != "GET":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    try:
        payload = LevelService.get_weekly_tasks(user)
        return JsonResponse(payload, status=200)
    except Exception as exc:
        return internal_error(exc)


@csrf_exempt
def claim_task(request, task_code):
    """POST /api/v1/tasks/<task_code>/claim — 领取已完成任务奖励"""
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    try:
        payload = LevelService.claim_task(user, task_code)
        return JsonResponse(payload, status=200)
    except LevelServiceError as exc:
        return error(exc.status, exc.message)
    except Exception as exc:
        return internal_error(exc)
