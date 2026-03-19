"""
Team Service - 队伍管理业务逻辑
"""

from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from core.models import Team, TeamMember, TeamInvitation, AppUser
from team_messaging.mapper.team_message_mapper import TeamMapper, TeamInvitationMapper


class TeamServiceError(Exception):
    """队伍业务异常"""

    def __init__(self, status, message):
        self.status = status
        self.message = message
        super().__init__(message)


class TeamService:

    def __init__(self):
        self.team_mapper = TeamMapper()
        self.invitation_mapper = TeamInvitationMapper()

    def create_team(self, owner, title="", description="", max_members=5):
        """创建队伍"""
        if not isinstance(owner, AppUser):
            raise TeamServiceError(400, "Invalid owner")

        team = self.team_mapper.create_team(
            owner=owner,
            title=title,
            description=description,
            max_members=max(2, min(max_members, 20)),  # 2-20人范围
        )
        return {
            "id": team.id,
            "owner_id": team.owner_id,
            "title": team.title,
            "description": team.description,
            "max_members": team.max_members,
            "status": team.status,
            "created_at": team.created_at.isoformat(),
        }

    def get_team_detail(self, user, team_id):
        """获取队伍详情"""
        team = self.team_mapper.get_team(team_id)
        if not team:
            raise TeamServiceError(404, "Team not found")

        members = self.team_mapper.get_team_members(team_id)
        member_count = self.team_mapper.get_team_member_count(team_id)

        return {
            "id": team.id,
            "owner_id": team.owner_id,
            "owner_nickname": team.owner.nickname,
            "title": team.title,
            "description": team.description,
            "max_members": team.max_members,
            "current_members": member_count,
            "status": team.status,
            "members": [
                {
                    "user_id": m.user_id,
                    "nickname": m.user.nickname,
                    "role": m.role,
                    "status": m.status,
                    "joined_at": m.joined_at.isoformat() if m.joined_at else None,
                }
                for m in members
            ],
            "created_at": team.created_at.isoformat(),
            "closed_at": team.closed_at.isoformat() if team.closed_at else None,
        }

    def update_team(self, user, team_id, title=None, description=None):
        """修改队伍信息（仅队长）"""
        team = self.team_mapper.get_team(team_id)
        if not team:
            raise TeamServiceError(404, "Team not found")

        if team.owner_id != user.id:
            raise TeamServiceError(403, "Only owner can update team")

        team = self.team_mapper.update_team(team, title=title, description=description)
        return {
            "id": team.id,
            "title": team.title,
            "description": team.description,
            "updated_at": team.updated_at.isoformat(),
        }

    def delete_team(self, user, team_id):
        """解散队伍（仅队长）"""
        team = self.team_mapper.get_team(team_id)
        if not team:
            raise TeamServiceError(404, "Team not found")

        if team.owner_id != user.id:
            raise TeamServiceError(403, "Only owner can delete team")

        team = self.team_mapper.update_team(team, status="closed")
        return {"id": team.id, "status": "closed"}

    def get_team_members(self, user, team_id):
        """获取队伍成员列表"""
        team = self.team_mapper.get_team(team_id)
        if not team:
            raise TeamServiceError(404, "Team not found")

        members = self.team_mapper.get_team_members(team_id)
        return {
            "team_id": team_id,
            "members": [
                {
                    "user_id": m.user_id,
                    "nickname": m.user.nickname,
                    "role": m.role,
                    "status": m.status,
                    "joined_at": m.joined_at.isoformat() if m.joined_at else None,
                }
                for m in members
            ],
        }

    def remove_team_member(self, user, team_id, user_id):
        """移除队伍成员（需要admin权限）"""
        team = self.team_mapper.get_team(team_id)
        if not team:
            raise TeamServiceError(404, "Team not found")

        # 验证操作者权限（队长或admin）
        operator_member = self.team_mapper.get_team_member(team_id, user.id)
        if not operator_member or operator_member.role not in ["admin"]:
            if team.owner_id != user.id:
                raise TeamServiceError(403, "Only admin can remove members")

        # 不能移除队长
        if user_id == team.owner_id:
            raise TeamServiceError(403, "Cannot remove team owner")

        member = self.team_mapper.remove_team_member(team_id, user_id)
        if not member:
            raise TeamServiceError(404, "Team member not found")

        return {"user_id": user_id, "status": "kicked"}

    def send_team_invitation(self, user, team_id, invitee_id):
        """
        发送队伍邀请（冷却规则）

        规则：
        - 同一队伍对同一人，第1、2次邀请无限制
        - 第3次及以后，需要距上次邀请至少10分钟
        """
        team = self.team_mapper.get_team(team_id)
        if not team:
            raise TeamServiceError(404, "Team not found")

        # 验证邀请者权限
        inviter_member = self.team_mapper.get_team_member(team_id, user.id)
        if not inviter_member:
            raise TeamServiceError(403, "You are not in this team")

        if inviter_member.role != "admin" and team.owner_id != user.id:
            raise TeamServiceError(403, "Only admin can send invitations")

        # 检查被邀请者
        try:
            invitee = AppUser.objects.get(id=invitee_id)
        except AppUser.DoesNotExist:
            raise TeamServiceError(404, "Invitee not found")

        # 检查被邀请者是否已在队伍中
        existing_member = self.team_mapper.get_team_member(team_id, invitee_id)
        if existing_member and existing_member.status in ["invited", "joined"]:
            raise TeamServiceError(400, "User is already in the team")

        # 检查队伍是否已满
        member_count = self.team_mapper.get_team_member_count(team_id)
        if member_count >= team.max_members:
            raise TeamServiceError(400, "Team is full")

        # 冷却检查 - 获取最后一次邀请
        last_invitation = self.invitation_mapper.get_last_invitation(
            team_id, invitee_id
        )

        if last_invitation and last_invitation.status == "pending":
            # 存在待处理邀请，检查冷却
            attempt_count = last_invitation.attempt_count

            if attempt_count >= 3:
                # 第3次及以后需要10分钟冷却
                last_time = last_invitation.last_invited_at
                cooldown_until = last_time + timedelta(minutes=10)
                now = timezone.now()

                if now < cooldown_until:
                    wait_minutes = (cooldown_until - now).total_seconds() / 60
                    raise TeamServiceError(
                        429,
                        f"Please wait {int(wait_minutes)} minutes before sending another invitation",
                    )

        # 创建邀请（自动增加attempt_count或重置为1）
        invitation = self.invitation_mapper.create_invitation(
            team_id=team_id,
            inviter=user,
            invitee=invitee,
            attempt_count=(
                1 if not last_invitation else last_invitation.attempt_count + 1
            ),
        )

        return {
            "invitation_id": invitation.id,
            "team_id": team_id,
            "invitee_id": invitee_id,
            "status": "pending",
            "created_at": invitation.created_at.isoformat(),
        }

    def check_invitation_cooldown(self, team_id, invitee_id):
        """检查邀请冷却状态（用于前端显示还需等待多久）"""
        last_invitation = self.invitation_mapper.get_last_invitation(
            team_id, invitee_id
        )

        if not last_invitation or last_invitation.status != "pending":
            return {"need_wait": False, "wait_minutes": 0}

        attempt_count = last_invitation.attempt_count
        if attempt_count < 3:
            return {"need_wait": False, "wait_minutes": 0}

        last_time = last_invitation.last_invited_at
        cooldown_until = last_time + timedelta(minutes=10)
        now = timezone.now()

        if now >= cooldown_until:
            return {"need_wait": False, "wait_minutes": 0}

        wait_seconds = (cooldown_until - now).total_seconds()
        wait_minutes = max(1, int(wait_seconds / 60))

        return {"need_wait": True, "wait_minutes": wait_minutes}

    def get_user_invitations(self, user, page=1, page_size=10):
        """获取用户的待处理邀请列表"""
        invitations = self.invitation_mapper.get_user_invitations(
            user.id, page=page, page_size=page_size
        )
        total_count = self.invitation_mapper.get_user_invitations_count(user.id)

        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "invitations": [
                {
                    "invitation_id": inv.id,
                    "team_id": inv.team_id,
                    "team_title": inv.team.title or f"{inv.team.owner.nickname}'s Team",
                    "inviter_nickname": inv.inviter.nickname,
                    "status": inv.status,
                    "created_at": inv.created_at.isoformat(),
                }
                for inv in invitations
            ],
        }

    @transaction.atomic
    def accept_invitation(self, user, invitation_id):
        """接受邀请"""
        invitation = (
            TeamInvitation.objects.select_related("team")
            .filter(id=invitation_id, invitee_id=user.id, status="pending")
            .first()
        )

        if not invitation:
            raise TeamServiceError(404, "Invitation not found or expired")

        team = invitation.team

        # 检查队伍是否已满
        member_count = self.team_mapper.get_team_member_count(team.id)
        if member_count >= team.max_members:
            raise TeamServiceError(400, "Team is now full")

        # 接受邀请
        self.invitation_mapper.accept_invitation(invitation_id)

        # 创建或更新成员记录
        member, created = TeamMember.objects.get_or_create(
            team_id=team.id,
            user_id=user.id,
            defaults={"role": "member", "status": "joined"},
        )

        if not created:
            member.status = "joined"
            member.joined_at = timezone.now()
            member.save()

        return {"team_id": team.id, "status": "accepted"}

    @transaction.atomic
    def reject_invitation(self, user, invitation_id):
        """拒绝邀请"""
        invitation = TeamInvitation.objects.filter(
            id=invitation_id, invitee_id=user.id, status="pending"
        ).first()

        if not invitation:
            raise TeamServiceError(404, "Invitation not found or expired")

        self.invitation_mapper.reject_invitation(invitation_id)

        return {"invitation_id": invitation_id, "status": "rejected"}


class TeamInvitationService:
    """组队邀请业务逻辑"""

    def __init__(self):
        pass

    # TODO: 实现以下方法
    # - send_invitation(team_id, inviter_id, invitee_id, message) - 检查冷却
    # - get_pending_invitations(user_id, page, page_size)
    # - accept_invitation(invitation_id) - 重置attempt_count
    # - reject_invitation(invitation_id)
    # - check_cooldown(team_id, invitee_id) -> bool/remaining_seconds
