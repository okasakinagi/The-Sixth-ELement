"""
Message Controller
处理消息、积分赠送等操作
"""

import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from core.views import error, require_auth
from team_messaging.service.message_service import (
    MessageService,
    PointsGiftService,
    MessageServiceError,
)


message_service = MessageService()
points_service = PointsGiftService()


def _parse_json(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def _parse_int(value, default=None):
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@csrf_exempt
@require_http_methods(["GET"])
def get_messages(request):
    """获取消息列表（分页、按type筛选）"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        page = _parse_int(request.GET.get("page"), default=1)
        page_size = _parse_int(request.GET.get("page_size"), default=20)
        message_type = request.GET.get("type")
        status = request.GET.get("status")

        result = message_service.get_messages(
            user,
            page=page,
            page_size=page_size,
            message_type=message_type,
            status=status,
        )
        return JsonResponse(result, status=200)
    except MessageServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["GET"])
def get_unread_count(request):
    """获取未读消息数（从Redis读取，缓存1小时）"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        result = message_service.get_unread_count(user)
        return JsonResponse(result, status=200)
    except MessageServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["PATCH"])
def mark_message_as_read(request, message_id):
    """标记消息已读"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        message_id = _parse_int(message_id)
        if not message_id:
            return error(400, "Invalid message_id")

        result = message_service.mark_as_read(user, message_id)
        return JsonResponse(result, status=200)
    except MessageServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_message(request, message_id):
    """删除消息"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        message_id = _parse_int(message_id)
        if not message_id:
            return error(400, "Invalid message_id")

        result = message_service.delete_message(user, message_id)
        return JsonResponse(result, status=200)
    except MessageServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["POST"])
def send_points_gift(request):
    """
    赠送积分（包含200分/天日限检查）

    请求参数：
    - receiver_id: 接收者ID
    - points_amount: 赠送点数
    - message: 可选的留言（默认为空）
    """
    user, err = require_auth(request)
    if err:
        return err

    try:
        data = _parse_json(request)

        receiver_id = _parse_int(data.get("receiver_id"))
        if not receiver_id:
            return error(400, "receiver_id is required")

        points_amount = _parse_int(data.get("points_amount"))
        if not points_amount:
            return error(400, "points_amount is required and must be positive")

        message = data.get("message", "")

        result = points_service.send_points_gift(
            sender=user,
            receiver_id=receiver_id,
            points_amount=points_amount,
            message=message,
        )
        return JsonResponse(result, status=200)
    except MessageServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["GET"])
def get_points_gift_limit(request):
    """获取积分赠送的日限额度信息"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        result = points_service.get_daily_gift_limit_info(user)
        return JsonResponse(result, status=200)
    except MessageServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")
