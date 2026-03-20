"""
Team Mapper
数据库查询层
"""

from django.db.models import Q
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta

from core.models import Team, TeamMember, TeamInvitation, Message, AppUser, PointsLog


class TeamMapper:
    """队伍数据查询"""

    @staticmethod
    def get_team(team_id):
        """获取队伍"""
        return Team.objects.select_related("owner").filter(id=team_id).first()

    @staticmethod
    def create_team(owner, title, description, max_members):
        """创建队伍"""
        team = Team.objects.create(
            owner=owner,
            title=title or f"{owner.nickname}'s Team",
            description=description,
            max_members=max_members,
        )
        # 队长自动加入
        TeamMember.objects.create(team=team, user=owner, role="owner", status="joined")
        return team

    @staticmethod
    def get_team_members(team_id):
        """获取队伍成员列表"""
        return (
            TeamMember.objects.select_related("user")
            .filter(team_id=team_id, status__in=["invited", "joined"])
            .order_by("joined_at")
        )

    @staticmethod
    def get_team_member_count(team_id):
        """获取队伍当前成员数（已加入）"""
        return TeamMember.objects.filter(team_id=team_id, status="joined").count()

    @staticmethod
    def get_team_member(team_id, user_id):
        """获取特定队伍成员"""
        return (
            TeamMember.objects.select_related("user")
            .filter(team_id=team_id, user_id=user_id)
            .first()
        )

    @staticmethod
    def update_team(team, title=None, description=None, status=None, max_members=None):
        """更新队伍信息"""
        if title is not None:
            team.title = title
        if description is not None:
            team.description = description
        if max_members is not None:
            team.max_members = max_members
        if status is not None:
            team.status = status
            if status == "closed":
                team.closed_at = timezone.now()
        team.save()
        return team

    @staticmethod
    def delete_team_members(team_id):
        """删除队伍所有成员"""
        TeamMember.objects.filter(team_id=team_id).delete()

    @staticmethod
    def remove_team_member(team_id, user_id):
        """移除队伍成员"""
        member = TeamMember.objects.filter(team_id=team_id, user_id=user_id).first()
        if member:
            member.status = "kicked"
            member.left_at = timezone.now()
            member.save()
        return member

    @staticmethod
    def set_team_member_role(team_id, user_id, role):
        """设置队伍成员角色"""
        member = TeamMember.objects.filter(team_id=team_id, user_id=user_id).first()
        if member:
            member.role = role
            member.save(update_fields=["role"])
        return member


class TeamInvitationMapper:
    """邀请数据查询"""

    @staticmethod
    def get_pending_invitation(team_id, invitee_id):
        """获取待处理邀请"""
        return TeamInvitation.objects.filter(
            team_id=team_id, invitee_id=invitee_id, status="pending"
        ).first()

    @staticmethod
    def get_last_invitation(team_id, invitee_id):
        """获取最后一次邀请（任何状态）"""
        return (
            TeamInvitation.objects.filter(team_id=team_id, invitee_id=invitee_id)
            .order_by("-created_at")
            .first()
        )

    @staticmethod
    def create_invitation(team_id, inviter, invitee, attempt_count=1):
        """创建或更新邀请"""
        invitation, created = TeamInvitation.objects.get_or_create(
            team_id=team_id,
            invitee_id=invitee.id,
            defaults={
                "inviter": inviter,
                "attempt_count": attempt_count,
                "status": "pending",
            },
        )
        if not created:
            # 已存在非pending则更新
            if invitation.status != "pending":
                invitation.status = "pending"
                invitation.attempt_count = attempt_count
                invitation.last_invited_at = timezone.now()
                invitation.save()
            else:
                # pending则增加attempt_count
                invitation.attempt_count += 1
                invitation.last_invited_at = timezone.now()
                invitation.save()
        return invitation

    @staticmethod
    def accept_invitation(invitation_id):
        """接受邀请"""
        invitation = TeamInvitation.objects.filter(id=invitation_id).first()
        if invitation:
            invitation.status = "accepted"
            invitation.accepted_at = timezone.now()
            invitation.attempt_count = 0  # 重置计数
            invitation.save()
        return invitation

    @staticmethod
    def reject_invitation(invitation_id):
        """拒绝邀请"""
        invitation = TeamInvitation.objects.filter(id=invitation_id).first()
        if invitation:
            invitation.status = "rejected"
            invitation.rejected_at = timezone.now()
            invitation.save()
        return invitation

    @staticmethod
    def get_user_invitations(user_id, page=1, page_size=10):
        """获取用户的待处理邀请（分页）"""
        offset = (page - 1) * page_size
        invitations = (
            TeamInvitation.objects.filter(invitee_id=user_id, status="pending")
            .select_related("team", "team__owner", "inviter")
            .order_by("-created_at")[offset : offset + page_size]
        )
        return invitations

    @staticmethod
    def get_user_invitations_count(user_id):
        """获取用户待处理邀请数"""
        return TeamInvitation.objects.filter(
            invitee_id=user_id, status="pending"
        ).count()


class MessageMapper:
    """消息数据查询"""

    @staticmethod
    def _bump_message_cache_version(user_id):
        """递增用户消息缓存版本号，失败时降级重置。"""
        if not user_id:
            return
        cache_key = f"user:{user_id}:messages_cache_version"
        try:
            cache.incr(cache_key)
        except Exception:
            try:
                current = cache.get(cache_key)
                cache.set(cache_key, (current or 0) + 1, timeout=86400)
            except Exception:
                pass

    @staticmethod
    def get_user_messages(
        user_id, page=1, page_size=20, message_type=None, status=None
    ):
        """获取用户消息列表（分页）"""
        offset = (page - 1) * page_size
        query = Message.objects.filter(user_id=user_id)
        if message_type:
            query = query.filter(message_type=message_type)
        if status:
            query = query.filter(status=status)
        messages = query.select_related("user", "sender").order_by("-created_at")[
            offset : offset + page_size
        ]
        return messages

    @staticmethod
    def get_user_messages_count(user_id, message_type=None, status=None):
        """获取用户消息总数"""
        query = Message.objects.filter(user_id=user_id)
        if message_type:
            query = query.filter(message_type=message_type)
        if status:
            query = query.filter(status=status)
        return query.count()

    @staticmethod
    def get_unread_message_count(user_id):
        """获取用户未读消息数"""
        return Message.objects.filter(user_id=user_id, status="unread").count()

    @staticmethod
    def create_message(
        user_id,
        sender_id,
        message_type,
        title,
        content,
        ref_type=None,
        ref_id=None,
        points_amount=0,
    ):
        """创建消息"""
        message = Message.objects.create(
            user_id=user_id,
            sender_id=sender_id,
            type=message_type,  # 保留兼容性
            message_type=message_type,
            title=title,
            content=content,
            status="unread",
            ref_type=ref_type,
            ref_id=ref_id,
            points_amount=points_amount,
        )
        MessageMapper._bump_message_cache_version(user_id)
        return message

    @staticmethod
    def mark_as_read(message_id):
        """标记消息已读"""
        message = Message.objects.filter(id=message_id).first()
        if message and message.status == "unread":
            message.status = "read"
            message.read_at = timezone.now()
            message.save()
            MessageMapper._bump_message_cache_version(message.user_id)
        return message

    @staticmethod
    def delete_message(message_id):
        """删除消息（标记为deleted）"""
        message = Message.objects.filter(id=message_id).first()
        if message:
            message.status = "deleted"
            message.save()
            MessageMapper._bump_message_cache_version(message.user_id)
        return message

    @staticmethod
    def get_message(message_id):
        """获取单条消息"""
        return (
            Message.objects.select_related("user", "sender")
            .filter(id=message_id)
            .first()
        )


class PointsMapper:
    """积分数据查询"""

    @staticmethod
    def get_daily_gift_total(user_id):
        """获取用户当天赠送积分总数"""
        today = timezone.now().date()
        logs = PointsLog.objects.filter(
            user_id=user_id, points_type="points_gift", created_at__date=today
        )
        total = sum(log.delta for log in logs if log.delta < 0)  # delta为负数表示扣款
        return abs(total)

    @staticmethod
    def create_points_log(
        user_id, points_type, delta, reason, ref_type=None, ref_id=None
    ):
        """创建积分日志"""
        log = PointsLog.objects.create(
            user_id=user_id,
            points_type=points_type,
            delta=delta,
            reason=reason,
            ref_type=ref_type,
            ref_id=ref_id,
        )
        return log
