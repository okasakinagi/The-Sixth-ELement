"""
Team Management Controller
处理队伍创建、邀请、成员管理等操作
"""

import json
import re
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from core.views import error, require_auth
from team_messaging.service.team_service import TeamService, TeamServiceError


service = TeamService()


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
@require_http_methods(["POST"])
def create_team(request):
    """创建队伍"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        data = _parse_json(request)
        result = service.create_team(
            owner=user,
            title=data.get("title", ""),
            description=data.get("description", ""),
            max_members=_parse_int(data.get("max_members"), default=5),
        )
        return JsonResponse(result, status=201)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["GET"])
def get_team_detail(request, team_id):
    """获取队伍详情"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        team_id = _parse_int(team_id)
        if not team_id:
            return error(400, "Invalid team_id")

        result = service.get_team_detail(user, team_id)
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["GET"])
def get_team_members(request, team_id):
    """获取队伍成员列表"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        team_id = _parse_int(team_id)
        if not team_id:
            return error(400, "Invalid team_id")

        result = service.get_team_members(user, team_id)
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["PATCH"])
def update_team(request, team_id):
    """修改队伍信息"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        team_id = _parse_int(team_id)
        if not team_id:
            return error(400, "Invalid team_id")

        data = _parse_json(request)
        result = service.update_team(
            user, team_id, title=data.get("title"), description=data.get("description")
        )
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_team(request, team_id):
    """解散队伍"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        team_id = _parse_int(team_id)
        if not team_id:
            return error(400, "Invalid team_id")

        result = service.delete_team(user, team_id)
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["DELETE"])
def remove_team_member(request, team_id, user_id):
    """移除队伍成员"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        team_id = _parse_int(team_id)
        user_id = _parse_int(user_id)
        if not team_id or not user_id:
            return error(400, "Invalid team_id or user_id")

        result = service.remove_team_member(user, team_id, user_id)
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["POST"])
def send_team_invitation(request, team_id):
    """发送队伍邀请（包含冷却检查）"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        team_id = _parse_int(team_id)
        if not team_id:
            return error(400, "Invalid team_id")

        data = _parse_json(request)
        invitee_id = _parse_int(data.get("invitee_id"))
        if not invitee_id:
            return error(400, "invitee_id is required")

        result = service.send_team_invitation(user, team_id, invitee_id)
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["GET"])
def get_invitations(request):
    """获取用户的待处理邀请列表"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        page = _parse_int(request.GET.get("page"), default=1)
        page_size = _parse_int(request.GET.get("page_size"), default=10)

        result = service.get_user_invitations(user, page=page, page_size=page_size)
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["PATCH"])
def accept_invitation(request, invitation_id):
    """接受邀请"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        invitation_id = _parse_int(invitation_id)
        if not invitation_id:
            return error(400, "Invalid invitation_id")

        result = service.accept_invitation(user, invitation_id)
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")


@csrf_exempt
@require_http_methods(["PATCH"])
def reject_invitation(request, invitation_id):
    """拒绝邀请"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        invitation_id = _parse_int(invitation_id)
        if not invitation_id:
            return error(400, "Invalid invitation_id")

        result = service.reject_invitation(user, invitation_id)
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return error(500, f"Internal server error: {str(e)}")
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def get_team_members(request, team_id):
    """获取队伍成员列表"""
    try:
        # TODO: 实现获取队伍成员
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PATCH"])
def update_team(request, team_id):
    """修改队伍信息（队长只）"""
    try:
        # TODO: 实现修改队伍
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_team(request, team_id):
    """解散队伍（队长只）"""
    try:
        # TODO: 实现解散队伍
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def remove_team_member(request, team_id, user_id):
    """移除队伍成员（队长/管理员）"""
    try:
        # TODO: 实现移除成员
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def send_team_invitation(request, team_id):
    """发送队伍邀请（检查10min冷却）"""
    try:
        # TODO: 实现发送邀请
        # 需要检查：
        # 1. 当前用户是否是队长或管理员
        # 2. 目标用户是否已在队伍中
        # 3. 是否已有待处理邀请
        # 4. 冷却时间检查（第1、2次无限制，3+需10分钟）
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def get_invitations(request):
    """获取待处理邀请列表"""
    try:
        # TODO: 实现获取邀请列表
        # 分页: page, page_size
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PATCH"])
def accept_invitation(request, invitation_id):
    """接受邀请（重置attempt_count，创建TeamMember）"""
    try:
        # TODO: 实现接受邀请
        # 创建TeamMember记录
        # 更新TeamInvitation状态为accepted
        # 更新Message为已读
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["PATCH"])
def reject_invitation(request, invitation_id):
    """拒绝邀请"""
    try:
        # TODO: 实现拒绝邀请
        pass
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
