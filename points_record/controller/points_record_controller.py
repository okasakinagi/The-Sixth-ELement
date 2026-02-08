"""
Points Record Controller - handles points record endpoints.
"""

import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.views import error, require_auth
from points_record.service.points_record_service import PointsRecordError, PointsRecordService


service = PointsRecordService()


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


@csrf_exempt
def points_summary(request):
    if request.method != "GET":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    try:
        payload = service.get_points_summary(user)
        return JsonResponse(payload, status=200)
    except PointsRecordError as exc:
        return error(exc.status, exc.message)
    except Exception as exc:
        return error(500, f"Internal server error: {str(exc)}")


@csrf_exempt
def points_logs(request):
    if request.method != "GET":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err

    filters = {
        "type": request.GET.get("type"),
        "start_date": request.GET.get("start_date"),
        "end_date": request.GET.get("end_date"),
        "keyword": request.GET.get("keyword"),
        "sort": request.GET.get("sort"),
        "page": _parse_int(request.GET.get("page"), default=1),
        "page_size": _parse_int(request.GET.get("page_size"), default=20),
    }
    try:
        payload = service.list_points_logs(user, filters)
        # 计算余额
        current_balance = user.points
        for item in reversed(payload["items"]):
            current_balance -= item["delta"]
            item["balance"] = current_balance
        return JsonResponse(payload, status=200)
    except PointsRecordError as exc:
        return error(exc.status, exc.message)
    except Exception as exc:
        return error(500, f"Internal server error: {str(exc)}")


@csrf_exempt
def update_points(request):
    if request.method != "POST":
        return error(405, "Method not allowed")
    user, err = require_auth(request)
    if err:
        return err
    
    try:
        data = _parse_json(request)
        delta = data.get("delta")
        reason = data.get("reason")
        ref_type = data.get("ref_type")
        ref_id = data.get("ref_id")
        
        payload = service.update_points(user, delta, reason, ref_type, ref_id)
        return JsonResponse(payload, status=200)
    except PointsRecordError as exc:
        return error(exc.status, exc.message)
    except Exception as exc:
        return error(500, f"Internal server error: {str(exc)}")
