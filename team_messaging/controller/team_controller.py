"""
Team Management Controller
处理队伍创建、邀请、成员管理等操作
"""

import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from core.views import error, internal_error, require_auth
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
        return internal_error(e)


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
        return internal_error(e)


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
        return internal_error(e)


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
            user,
            team_id,
            title=data.get("title"),
            description=data.get("description"),
            max_members=_parse_int(data.get("max_members")),
        )
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return internal_error(e)


@csrf_exempt
@require_http_methods(["PATCH"])
def set_member_role(request, team_id, user_id):
    """设置成员角色（队长可任命/取消管理员）"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        team_id = _parse_int(team_id)
        user_id = _parse_int(user_id)
        if not team_id or not user_id:
            return error(400, "队伍ID或用户ID无效")

        data = _parse_json(request)
        role = (data.get("role") or "").strip()
        if not role:
            return error(400, "角色不能为空")

        result = service.set_team_member_role(user, team_id, user_id, role)
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return internal_error(e)


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
        return internal_error(e)


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
        return internal_error(e)


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
        return internal_error(e)


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
        return internal_error(e)


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
        return internal_error(e)


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
        return internal_error(e)


@csrf_exempt
@require_http_methods(["GET"])
def get_my_team(request):
    """★ Phase 2: 获取用户唯一的队伍（单队伍模式）"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        result = service.get_my_team(user)
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return internal_error(e)


@csrf_exempt
@require_http_methods(["GET"])
def check_invitation_cooldown(request, team_id, invitee_id):
    """检查邀请冷却状态（用于前端显示倒计时）"""
    user, err = require_auth(request)
    if err:
        return err

    try:
        team_id = _parse_int(team_id)
        invitee_id = _parse_int(invitee_id)
        if not team_id or not invitee_id:
            return error(400, "Invalid team_id or invitee_id")

        result = service.check_invitation_cooldown(team_id, invitee_id)
        return JsonResponse(result, status=200)
    except TeamServiceError as e:
        return error(e.status, e.message)
    except Exception as e:
        return internal_error(e)
