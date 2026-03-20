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
        """创建队伍 (Phase 2: 单队伍模式 - 创建前检查用户是否已在队伍中)"""
        if not isinstance(owner, AppUser):
            raise TeamServiceError(400, "Invalid owner")

        # ★ Phase 2: 检查用户是否已在其他队伍中（已joined）
        existing_team = (
            TeamMember.objects.filter(user_id=owner.id, status="joined")
            .select_related("team")
            .first()
        )
        if existing_team:
            raise TeamServiceError(
                400,
                f"Already in team '{existing_team.team.title}', leave first to create a new one",
            )

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
            raise TeamServiceError(404, "队伍不存在")

        members = self.team_mapper.get_team_members(team_id)
        member_count = self.team_mapper.get_team_member_count(team_id)

        return {
            "id": team.id,
            "owner_id": team.owner_id,
            "owner_nickname": team.owner.nickname,
            "title": team.title,
            "description": team.description,
            "icon": getattr(team, "icon", "🛡️"),
            "max_members": team.max_members,
            "current_members": member_count,
            "status": team.status,
            "members": [
                {
                    "id": m.id,
                    "user_id": m.user_id,
                    "user_nickname": m.user.nickname,
                    "nickname": m.user.nickname,
                    "role": "owner" if m.user_id == team.owner_id else m.role,
                    "status": m.status,
                    "joined_at": m.joined_at.isoformat() if m.joined_at else None,
                }
                for m in members
            ],
            "created_at": team.created_at.isoformat(),
            "closed_at": team.closed_at.isoformat() if team.closed_at else None,
        }

    def get_my_team(self, user):
        """★ Phase 2: 获取用户唯一的队伍（单队伍模式）"""
        member = (
            TeamMember.objects.filter(
                user_id=user.id, status="joined", team__status="active"
            )
            .select_related("team")
            .first()
        )

        if not member:
            return {"team": None, "my_role": None, "members_count": 0}

        team = member.team
        members = self.team_mapper.get_team_members(team.id)
        member_count = self.team_mapper.get_team_member_count(team.id)

        return {
            "team": {
                "id": team.id,
                "owner_id": team.owner_id,
                "title": team.title,
                "description": team.description,
                "icon": getattr(team, "icon", "🛡️"),  # 从模型获取icon字段
                "max_members": team.max_members,
                "members_count": member_count,
                "status": team.status,
                "created_at": team.created_at.isoformat(),
            },
            "my_role": "owner" if team.owner_id == user.id else member.role,
            "members": [
                {
                    "id": m.id,
                    "user_id": m.user_id,
                    "user_nickname": m.user.nickname,
                    "role": "owner" if m.user_id == team.owner_id else m.role,
                    "status": m.status,
                    "joined_at": m.joined_at.isoformat() if m.joined_at else None,
                }
                for m in members
            ],
        }

    def update_team(
        self, user, team_id, title=None, description=None, max_members=None
    ):
        """修改队伍信息（仅队长）"""
        team = self.team_mapper.get_team(team_id)
        if not team:
            raise TeamServiceError(404, "队伍不存在")

        if team.owner_id != user.id:
            raise TeamServiceError(403, "仅队长可修改队伍信息")

        normalized_max_members = None
        if max_members is not None:
            normalized_max_members = max(2, min(int(max_members), 20))
            joined_count = TeamMember.objects.filter(
                team_id=team_id, status="joined"
            ).count()
            if normalized_max_members < joined_count:
                raise TeamServiceError(
                    400, f"人数上限不能小于当前已加入人数（{joined_count}）"
                )

        team = self.team_mapper.update_team(
            team,
            title=title,
            description=description,
            max_members=normalized_max_members,
        )
        return {
            "id": team.id,
            "title": team.title,
            "description": team.description,
            "max_members": team.max_members,
            "updated_at": team.updated_at.isoformat(),
        }

    @transaction.atomic
    def delete_team(self, user, team_id):
        """解散队伍（仅队长）"""
        team = self.team_mapper.get_team(team_id)
        if not team:
            raise TeamServiceError(404, "队伍不存在")

        if team.owner_id != user.id:
            raise TeamServiceError(403, "仅队长可解散队伍")

        now = timezone.now()
        TeamMember.objects.filter(
            team_id=team_id, status__in=["joined", "invited"]
        ).update(
            status="left",
            left_at=now,
        )
        TeamInvitation.objects.filter(team_id=team_id, status="pending").update(
            status="expired"
        )

        team = self.team_mapper.update_team(team, status="closed")
        return {"id": team.id, "status": "closed"}

    def get_team_members(self, user, team_id):
        """获取队伍成员列表"""
        team = self.team_mapper.get_team(team_id)
        if not team:
            raise TeamServiceError(404, "队伍不存在")

        members = self.team_mapper.get_team_members(team_id)
        return {
            "team_id": team_id,
            "members": [
                {
                    "id": m.id,
                    "user_id": m.user_id,
                    "user_nickname": m.user.nickname,
                    "nickname": m.user.nickname,
                    "role": "owner" if m.user_id == team.owner_id else m.role,
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
            raise TeamServiceError(404, "队伍不存在")

        # 允许普通成员主动退出自己的队伍
        if user_id == user.id:
            self_member = self.team_mapper.get_team_member(team_id, user.id)
            if not self_member or self_member.status != "joined":
                raise TeamServiceError(404, "你不在该队伍中")
            if team.owner_id == user.id:
                raise TeamServiceError(403, "队长不能直接退出，请先解散队伍")
            self_member.status = "left"
            self_member.left_at = timezone.now()
            self_member.save(update_fields=["status", "left_at"])
            return {"user_id": user_id, "status": "left"}

        # 验证操作者权限（队长或admin）
        operator_member = self.team_mapper.get_team_member(team_id, user.id)
        if not operator_member or operator_member.role not in ["admin"]:
            if team.owner_id != user.id:
                raise TeamServiceError(403, "仅队长或管理员可移除成员")

        # 不能移除队长
        if user_id == team.owner_id:
            raise TeamServiceError(403, "不能移除队长")

        member = self.team_mapper.remove_team_member(team_id, user_id)
        if not member:
            raise TeamServiceError(404, "队伍成员不存在")

        return {"user_id": user_id, "status": "kicked"}

    def set_team_member_role(self, user, team_id, user_id, role):
        """设置成员角色（仅队长）"""
        team = self.team_mapper.get_team(team_id)
        if not team:
            raise TeamServiceError(404, "队伍不存在")

        if team.owner_id != user.id:
            raise TeamServiceError(403, "仅队长可任命管理员")

        if user_id == team.owner_id:
            raise TeamServiceError(400, "队长角色不可修改")

        if role not in ["admin", "member"]:
            raise TeamServiceError(400, "无效角色，仅支持 admin 或 member")

        member = self.team_mapper.get_team_member(team_id, user_id)
        if not member or member.status != "joined":
            raise TeamServiceError(404, "队伍成员不存在")

        member = self.team_mapper.set_team_member_role(team_id, user_id, role)
        return {
            "team_id": team_id,
            "user_id": user_id,
            "role": member.role,
            "message": "角色设置成功",
        }

    def send_team_invitation(self, user, team_id, invitee_id):
        """
        发送队伍邀请（冷却规则）

        规则：
        - 同一队伍对同一人，第1、2次邀请无限制
        - 第3次及以后，需要距上次邀请至少10分钟
        """
        team = self.team_mapper.get_team(team_id)
        if not team:
            raise TeamServiceError(404, "队伍不存在")

        # 验证邀请者权限
        inviter_member = self.team_mapper.get_team_member(team_id, user.id)
        if not inviter_member:
            raise TeamServiceError(403, "你不在该队伍中")

        if inviter_member.role != "admin" and team.owner_id != user.id:
            raise TeamServiceError(403, "仅队长或管理员可发送邀请")

        # 检查被邀请者
        try:
            invitee = AppUser.objects.get(id=invitee_id)
        except AppUser.DoesNotExist:
            raise TeamServiceError(404, "被邀请用户不存在")

        if invitee.id == user.id:
            raise TeamServiceError(400, "不能邀请自己")

        # 检查被邀请者是否已在队伍中
        existing_member = self.team_mapper.get_team_member(team_id, invitee_id)
        if existing_member and existing_member.status in ["invited", "joined"]:
            raise TeamServiceError(400, "该用户已在队伍中")

        # 检查队伍是否已满
        member_count = self.team_mapper.get_team_member_count(team_id)
        if member_count >= team.max_members:
            raise TeamServiceError(400, "队伍人数已满")

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
                        f"邀请过于频繁，请在 {int(wait_minutes)} 分钟后再试",
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

        # 创建邀请消息（ref_id存invitation_id，用于同步更新）
        from team_messaging.mapper.team_message_mapper import MessageMapper

        msg_mapper = MessageMapper()
        msg = msg_mapper.create_message(
            user_id=invitee_id,
            sender_id=user.id,
            message_type="team_invite",
            title=f"{user.nickname} 邀请你加入队伍 {team.title or '未命名队伍'}",
            content=f"你收到了来自 {user.nickname} 的队伍邀请。",
            ref_type="team_invite",
            ref_id=invitation.id,  # ★ 存invitation_id，而不是team_id
        )

        # 给邀请发起人创建系统回执，避免被识别为“对方发来的邀请”
        msg_mapper.create_message(
            user_id=user.id,
            sender_id=None,
            message_type="system",
            title="邀请已发送",
            content=f"已向 {invitee.nickname} 发送队伍邀请，等待对方处理。",
            ref_type="team_invite",
            ref_id=invitation.id,
        )

        # 给邀请方在与该好友会话中也保留一条邀请记录，便于追踪邀请进度
        msg_mapper.create_message(
            user_id=user.id,
            sender_id=invitee_id,
            message_type="system",
            title="队伍邀请记录",
            content=f"你已邀请 {invitee.nickname} 加入队伍，正在等待对方处理。",
            ref_type="team_invite",
            ref_id=invitation.id,
        )

        return {
            "invitation_id": invitation.id,
            "message_id": msg.id,
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
        """
        接受邀请
        ★ Phase 2: 如果用户已在其他队伍，自动从旧队伍退出，加入新队伍
        """
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

        # ★ Phase 2: 自动退出旧队伍（如果用户在其他队伍）
        old_member = (
            TeamMember.objects.filter(user_id=user.id, status="joined")
            .exclude(team_id=team.id)
            .first()
        )
        if old_member:
            old_member.status = "left"
            old_member.left_at = timezone.now()
            old_member.save()

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

        # ★ 同步更新对应的消息为已接受
        from team_messaging.mapper.team_message_mapper import MessageMapper
        from core.models import Message

        msg_mapper = MessageMapper()
        msg = Message.objects.filter(
            ref_type="team_invite",
            ref_id=invitation_id,
            user_id=user.id,
        ).first()
        if msg:
            msg.is_accepted = True
            msg.status = "read"
            msg.read_at = timezone.now()
            msg.save()

        Message.objects.filter(
            ref_type="team_invite",
            ref_id=invitation_id,
            user_id=user.id,
        ).update(
            is_accepted=True,
            status="read",
            read_at=timezone.now(),
        )

        # 给被邀请者发送显式系统提示：组队后填写积分将记入队长统计
        msg_mapper.create_message(
            user_id=user.id,
            sender_id=team.owner_id,
            message_type="system",
            title="已加入队伍",
            content="你已成功加入队伍。组队后你填写问卷获得的积分会自动记录到队长的账户中。",
            ref_type="team",
            ref_id=team.id,
        )

        # 给队长发送成员加入提示
        msg_mapper.create_message(
            user_id=team.owner_id,
            sender_id=user.id,
            message_type="system",
            title="新成员已加入",
            content=f"{user.nickname} 已加入你的队伍。该成员后续填写问卷积分将计入你的账户。",
            ref_type="team",
            ref_id=team.id,
        )

        return {"team_id": team.id, "status": "accepted"}

    @transaction.atomic
    def reject_invitation(self, user, invitation_id):
        """拒绝邀请"""
        invitation = (
            TeamInvitation.objects.select_related("team", "inviter")
            .filter(id=invitation_id, invitee_id=user.id, status="pending")
            .first()
        )

        if not invitation:
            raise TeamServiceError(404, "Invitation not found or expired")

        self.invitation_mapper.reject_invitation(invitation_id)

        from team_messaging.mapper.team_message_mapper import MessageMapper
        from core.models import Message

        msg_mapper = MessageMapper()

        Message.objects.filter(
            ref_type="team_invite",
            ref_id=invitation_id,
            user_id=user.id,
        ).update(
            status="read",
            read_at=timezone.now(),
        )

        msg_mapper.create_message(
            user_id=user.id,
            sender_id=invitation.inviter_id,
            message_type="system",
            title="已拒绝邀请",
            content=f"你已拒绝加入 {invitation.team.title or '该队伍'}。",
            ref_type="team",
            ref_id=invitation.team_id,
        )

        msg_mapper.create_message(
            user_id=invitation.inviter_id,
            sender_id=user.id,
            message_type="system",
            title="邀请已被拒绝",
            content=f"{user.nickname} 拒绝了加入队伍 {invitation.team.title or '该队伍'} 的邀请。",
            ref_type="team",
            ref_id=invitation.team_id,
        )

        return {"invitation_id": invitation_id, "status": "rejected"}


class TeamInvitationService:
    """组队邀请业务逻辑"""

    def __init__(self):
        pass
