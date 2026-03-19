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
    """获取未读消息数（从Redis缓存）"""
    try:
        # TODO: 实现获取未读数
        # 优先从Redis读取，miss时从DB查询后写回Redis
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PATCH"])
def mark_message_as_read(request, message_id):
    """标记消息已读"""
    try:
        # TODO: 实现标记已读
        # 更新Message.status='read', Message.read_at
        # 更新Redis unread_count
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_message(request, message_id):
    """删除消息"""
    try:
        # TODO: 实现删除消息
        # 标记为deleted或直接删除
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def send_points_gift(request):
    """赠送积分（检查200分日限额）"""
    try:
        # TODO: 实现赠送积分
        # 参数:
        # - receiver_id: 接收者ID
        # - points_amount: 赠送积分数
        # - message: 留言（可选）
        # 需要检查：
        # 1. 发送者积分充足
        # 2. 接收者存在
        # 3. 不能给自己转账
        # 4. 查询今日已赠送总额，检查是否超过200分
        # 5. 事务保护：扣减发送者 + 增加接收者 + 创建2条PointsLog + 创建Message
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
